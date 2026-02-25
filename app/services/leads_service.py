import csv
import io
import json
import asyncio
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.rbac import normalize_role
from app.models.follow_up_record import FollowUpRecord
from app.models.lead import Lead
from app.models.pool_transfer_log import PoolTransferLog
from app.models.user import User
from app.repositories import leads_repository, settings_repository
from app.schemas.lead import FollowUpCreate, LeadCreate, LeadUpdate


logger = logging.getLogger(__name__)


@dataclass
class AiRuntimeConfig:
    enabled: bool
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int
    max_input_chars: int


async def _resolve_ai_runtime_config(session: AsyncSession) -> AiRuntimeConfig:
    platform_setting = None
    try:
        platform_setting = await settings_repository.get_platform_setting(session)
    except Exception:
        platform_setting = None

    if platform_setting is None:
        return AiRuntimeConfig(
            enabled=settings.ai_enabled,
            api_key=(settings.ai_api_key or "").strip(),
            base_url=(settings.ai_base_url or "https://api.openai.com/v1").strip() or "https://api.openai.com/v1",
            model=(settings.ai_model or "gpt-4o-mini").strip() or "gpt-4o-mini",
            timeout_seconds=int(settings.ai_timeout_seconds),
            max_input_chars=int(settings.ai_max_input_chars),
        )

    return AiRuntimeConfig(
        enabled=bool(platform_setting.ai_enabled),
        api_key=(platform_setting.ai_api_key or "").strip(),
        base_url=(platform_setting.ai_base_url or "https://api.openai.com/v1").strip() or "https://api.openai.com/v1",
        model=(platform_setting.ai_model or "gpt-4o-mini").strip() or "gpt-4o-mini",
        timeout_seconds=int(platform_setting.ai_timeout_seconds or settings.ai_timeout_seconds),
        max_input_chars=int(settings.ai_max_input_chars),
    )


_HEADER_ALIASES: dict[str, list[str]] = {
    "name": ["name", "客户姓名", "姓名"],
    "phone": ["phone", "手机号码", "手机号", "电话"],
    "source": ["source", "来源渠道", "来源"],
    "project": ["project", "项目", "项目名称"],
    "status": ["status", "跟进状态", "状态"],
    "level": ["level", "意向评级", "意向等级"],
    "owner": ["owner", "归属销售", "归属人", "负责人"],
    "tags": ["tags", "客户标签", "标签"],
    "last_follow_up": ["lastFollowUp", "最后跟进时间"],
    "dynamic_data": ["dynamicData", "扩展字段JSON", "扩展字段"],
    "follow_up_content": ["followUpContent", "跟进记录", "跟进内容"],
    "follow_up_type": ["followUpType", "跟进方式", "跟进类型"],
    "follow_up_operator": ["followUpOperator", "跟进人"],
    "follow_up_time": ["followUpTime", "跟进时间"],
}


_SOURCE_ALIASES: dict[str, str] = {
    "抖音广告": "douyin",
    "douying": "douyin",
    "douyin": "douyin",
    "百度搜索": "baidu",
    "baidu": "baidu",
    "转介绍": "referral",
    "referral": "referral",
    "线下展会": "expo",
    "expo": "expo",
    "手动录入": "manual",
    "manual": "manual",
}


_STATUS_ALIASES: dict[str, str] = {
    "待跟进": "pending",
    "pending": "pending",
    "初步沟通": "communicating",
    "communicating": "communicating",
    "深度跟进": "deep_following",
    "deep_following": "deep_following",
    "已邀约": "invited",
    "invited": "invited",
    "已到访": "visited",
    "visited": "visited",
    "已交定金": "deposit_paid",
    "deposit_paid": "deposit_paid",
    "已签约": "signed",
    "signed": "signed",
    "无效线索": "invalid",
    "无效客户": "invalid",
    "invalid": "invalid",
    "战败流失": "lost",
    "lost": "lost",
}


_SOURCE_EXPORT_LABELS: dict[str, str] = {
    "douyin": "抖音广告",
    "baidu": "百度搜索",
    "referral": "转介绍",
    "expo": "线下展会",
    "manual": "手动录入",
}


_STATUS_EXPORT_LABELS: dict[str, str] = {
    "pending": "待跟进",
    "communicating": "初步沟通",
    "deep_following": "深度跟进",
    "invited": "已邀约",
    "visited": "已到访",
    "deposit_paid": "已交定金",
    "signed": "已签约",
    "invalid": "无效客户",
    "lost": "战败流失",
}


_BASE_EXPORT_FIELD_CODES: set[str] = {
    "customer_name",
    "phone",
    "source",
    "project",
    "status",
    "level",
}


_AI_SCENE_GUIDANCE: dict[str, str] = {
    "pending": "目标是完成招商加盟客户首次有效触达，确认客户加盟动机、预算区间与沟通窗口。",
    "communicating": "目标是把招商沟通从泛聊推进到有效评估，明确加盟条件匹配度与下一步动作。",
    "deep_following": "目标是围绕加盟政策、选址与回本预期推进决策，识别卡点并给出推进节奏。",
    "invited": "目标是把邀约转化为到访或线上项目会，建议包含具体时间锚点和确认动作。",
    "visited": "目标是到访/面谈后推进签约意向，聚焦政策解释、异议处理与签约前准备。",
    "deposit_paid": "目标是推动正式签约，确认合同流程、回款节点与开店筹备事项。",
    "signed": "目标是做好签约后服务承接并促进转介绍，建议简洁并强调支持动作。",
    "invalid": "目标是礼貌收尾并保留二次激活机会，避免无效消耗。",
    "lost": "目标是低打扰挽回招商客户，优先识别流失原因并给出最小试探动作。",
}


def _field_value(row: dict[str, Any], key: str) -> str:
    aliases = _HEADER_ALIASES.get(key, [key])
    for alias in aliases:
        if alias in row and row[alias] is not None:
            return str(row[alias]).strip()
    return ""


def _normalize_source(value: str) -> str:
    text = value.strip()
    if not text:
        return text
    return _SOURCE_ALIASES.get(text, text)


def _normalize_status(value: str) -> str:
    text = value.strip()
    if not text:
        return "pending"
    return _STATUS_ALIASES.get(text, text)


def _normalize_level(value: str) -> str:
    text = value.strip().upper()
    if not text:
        return "C"
    if text in {"A", "B", "C", "D"}:
        return text
    if text.startswith("意向") and len(text) >= 3:
        candidate = text[-1]
        if candidate in {"A", "B", "C", "D"}:
            return candidate
    return "C"


def _parse_datetime(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    normalized = text.replace("/", "-")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _to_lead_dict(lead: Lead) -> dict[str, Any]:
    return {
        "id": lead.id,
        "name": lead.name,
        "phone": lead.phone,
        "project": lead.project,
        "source": lead.source,
        "status": lead.status,
        "level": lead.level,
        "owner": lead.owner_id,
        "createdAt": lead.created_at.isoformat(sep=" ") if lead.created_at else None,
        "lastFollowUp": lead.last_follow_up.isoformat(sep=" ") if lead.last_follow_up else None,
        "tags": lead.tags,
        "dynamicData": lead.dynamic_data,
    }


def _to_record_dict(record: FollowUpRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "leadId": record.lead_id,
        "type": record.type,
        "content": record.content,
        "operator": record.operator,
        "timestamp": record.timestamp.isoformat(sep=" "),
        "audioUrl": record.audio_url,
        "aiAnalysis": record.ai_analysis,
    }


async def list_leads(
    session: AsyncSession,
    *,
    current_staff: dict[str, Any] | None,
    page: int,
    page_size: int,
    keyword: str | None,
    status: str | None,
    source: str | None,
) -> dict[str, Any]:
    owner_id: str | None = None
    owner_ids: list[str] | None = None
    if current_staff is not None:
        role = normalize_role(str(current_staff.get("role") or ""))
        if role == "sales":
            owner_id = str(current_staff.get("staffId") or "")
        elif role == "manager":
            actor = await _get_actor_user(session, current_staff)
            if actor is None or not actor.dept_name:
                return {"list": [], "total": 0}
            dept_users = await leads_repository.list_users_by_department(session, actor.dept_name)
            owner_ids = [user.id for user in dept_users]

    base_query = leads_repository.build_leads_query(
        keyword,
        status,
        source,
        owner_id=owner_id,
        owner_ids=owner_ids,
        exclude_pool=True,
    )
    total = await leads_repository.count_leads(session, base_query)
    leads = await leads_repository.list_leads(session, base_query, page, page_size)

    return {
        "list": [_to_lead_dict(lead) for lead in leads],
        "total": int(total or 0),
    }


async def get_lead_detail(
    session: AsyncSession,
    lead_id: str,
    current_staff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lead = await leads_repository.get_lead(session, lead_id)
    if lead is None:
        raise AppException("客户不存在", business_code=400, status_code=404)
    await _ensure_lead_access(session, lead, current_staff)

    records = await leads_repository.list_follow_ups(session, lead_id)

    return {
        "lead": _to_lead_dict(lead),
        "timeline": [_to_record_dict(record) for record in records],
    }


async def _generate_lead_id(session: AsyncSession) -> str:
    prefix = leads_repository.build_lead_id_prefix(datetime.now(timezone.utc))
    count_today = await leads_repository.count_daily_leads(session, prefix)
    serial = count_today + 1
    return f"{prefix}{serial:04d}"


async def create_lead(
    session: AsyncSession,
    payload: LeadCreate,
    current_staff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    owner_id = payload.owner
    if current_staff is not None:
        role = normalize_role(str(current_staff.get("role") or ""))
        actor_staff_id = str(current_staff.get("staffId") or "")
        if role == "sales":
            if owner_id and owner_id != actor_staff_id:
                raise AppException("销售仅可录入归属到本人", business_code=400, status_code=403)
            owner_id = actor_staff_id
        elif role == "manager" and owner_id:
            target_staff = await leads_repository.get_user(session, owner_id)
            if target_staff is None:
                raise AppException("目标员工不存在", business_code=400, status_code=404)
            await _ensure_owner_assignment_permission(
                session,
                current_staff=current_staff,
                target_staff=target_staff,
            )

    lead_id = await _generate_lead_id(session)
    lead = Lead(
        id=lead_id,
        name=payload.name,
        phone=payload.phone,
        project=payload.project,
        source=payload.source,
        status=payload.status,
        level=payload.level,
        owner_id=owner_id,
        last_follow_up=payload.last_follow_up,
        tags=payload.tags,
        dynamic_data=payload.dynamic_data,
    )
    leads_repository.add_lead(session, lead)
    await leads_repository.commit(session)
    await leads_repository.refresh(session, lead)
    return _to_lead_dict(lead)


async def update_lead(
    session: AsyncSession,
    lead_id: str,
    payload: LeadUpdate,
    current_staff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lead = await leads_repository.get_lead(session, lead_id)
    if lead is None:
        raise AppException("客户不存在", business_code=400, status_code=404)
    await _ensure_lead_access(session, lead, current_staff)

    updates = payload.model_dump(exclude_none=True)
    if "owner" in updates and updates["owner"]:
        target_staff = await leads_repository.get_user(session, updates["owner"])
        if target_staff is None:
            raise AppException("目标员工不存在", business_code=400, status_code=404)
        if target_staff.active is False:
            raise AppException("目标员工已停用", business_code=400, status_code=400)
        if current_staff is not None:
            await _ensure_owner_assignment_permission(
                session,
                current_staff=current_staff,
                target_staff=target_staff,
            )

    for key, value in updates.items():
        if key == "owner":
            setattr(lead, "owner_id", value)
        else:
            setattr(lead, key, value)

    await leads_repository.commit(session)
    await leads_repository.refresh(session, lead)
    return _to_lead_dict(lead)


async def delete_lead(
    session: AsyncSession,
    lead_id: str,
    current_staff: dict[str, Any] | None = None,
) -> None:
    lead = await leads_repository.get_lead(session, lead_id)
    if lead is None:
        raise AppException("客户不存在", business_code=400, status_code=404)
    await _ensure_lead_access(session, lead, current_staff)

    await leads_repository.delete_follow_ups_by_lead(session, lead_id)
    await leads_repository.delete_lead(session, lead)
    await leads_repository.commit(session)


async def create_follow_up(
    session: AsyncSession,
    lead_id: str,
    payload: FollowUpCreate,
    current_staff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lead = await leads_repository.get_lead(session, lead_id)
    if lead is None:
        raise AppException("客户不存在", business_code=400, status_code=404)
    await _ensure_lead_access(session, lead, current_staff)

    record = FollowUpRecord(
        lead_id=lead_id,
        type=payload.type,
        content=payload.content,
        operator=payload.operator,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
        audio_url=payload.audio_url,
        ai_analysis=payload.ai_analysis,
    )
    leads_repository.add_follow_up(session, record)
    lead.last_follow_up = record.timestamp
    await leads_repository.commit(session)
    await leads_repository.refresh(session, record)
    await leads_repository.refresh(session, lead)
    return _to_record_dict(record)


async def _build_ai_suggestion_payload(
    lead: Lead,
    follow_ups: list[FollowUpRecord],
    user_goal: str | None,
    max_input_chars: int,
) -> dict[str, Any]:
    latest_follow_up = follow_ups[-1] if follow_ups else None
    latest_content = (latest_follow_up.content if latest_follow_up else "暂无历史跟进") or "暂无历史跟进"
    latest_content = latest_content.strip()[:max_input_chars]
    goal = (user_goal or "推进下一次有效触达").strip()[:200]

    status_text = str(getattr(lead, "status", "pending") or "pending")
    source_text = str(getattr(lead, "source", "manual") or "manual")
    evidence = [
        f"当前状态：{status_text}",
        f"来源渠道：{source_text}",
        f"最近跟进摘要：{latest_content}",
    ]

    return {
        "nextSentence": f"我理解您当前关注点，我们先围绕{goal}快速确认一个可执行时间。",
        "nextAction": "在24小时内发出到访或复沟通邀约，并确认具体时间窗口。",
        "riskPoints": [
            "最近跟进内容信息密度不足，后续行动可能模糊",
            "若48小时内无再次触达，客户活跃度可能继续下降",
        ],
        "recommendedScript": "您好，结合您之前的关注点，我这边给您准备了两个推进方案，您看今天晚些时候方便电话细聊3分钟吗？",
        "confidence": 0.72,
        "evidence": evidence,
        "model": "skeleton-v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


def _build_recent_follow_ups_digest(follow_ups: list[FollowUpRecord], max_input_chars: int) -> str:
    if not follow_ups:
        return "暂无历史跟进"
    snippets: list[str] = []
    recent_follow_ups = follow_ups[-3:]
    for item in recent_follow_ups:
        ts = item.timestamp.isoformat(sep=" ", timespec="minutes") if item.timestamp else "未知时间"
        item_type = str(getattr(item, "type", "other") or "other")
        content = str(getattr(item, "content", "") or "").strip()
        if not content:
            continue
        snippets.append(f"[{ts}][{item_type}] {content}")
    if not snippets:
        return "暂无历史跟进"
    return "\n".join(snippets)[:max_input_chars]


def _extract_json_payload(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _validate_ai_suggestion_payload(payload: dict[str, Any], *, fallback_model: str) -> dict[str, Any]:
    required_keys = [
        "nextSentence",
        "nextAction",
        "riskPoints",
        "recommendedScript",
        "confidence",
        "evidence",
    ]
    for key in required_keys:
        if key not in payload:
            raise AppException("AI返回格式异常，请稍后重试", business_code=400, status_code=502)
    return {
        "nextSentence": str(payload.get("nextSentence") or ""),
        "nextAction": str(payload.get("nextAction") or ""),
        "riskPoints": [str(item) for item in (payload.get("riskPoints") or [])],
        "recommendedScript": str(payload.get("recommendedScript") or ""),
        "confidence": float(payload.get("confidence") or 0.0),
        "evidence": [str(item) for item in (payload.get("evidence") or [])],
        "model": str(payload.get("model") or fallback_model),
        "generatedAt": str(payload.get("generatedAt") or datetime.now(timezone.utc).isoformat()),
    }


def _build_ai_context(
    lead: Lead,
    follow_ups: list[FollowUpRecord],
    user_goal: str | None,
    *,
    max_input_chars: int,
) -> dict[str, str]:
    latest_follow_up = follow_ups[-1] if follow_ups else None
    latest_content = (latest_follow_up.content if latest_follow_up else "暂无历史跟进") or "暂无历史跟进"
    latest_content = latest_content.strip()[:max_input_chars]
    goal = (user_goal or "推进下一次有效触达").strip()[:200]
    status_key = str(getattr(lead, "status", "pending") or "pending")
    status_label = _STATUS_EXPORT_LABELS.get(status_key, status_key)
    scene_guidance = _AI_SCENE_GUIDANCE.get(status_key, _AI_SCENE_GUIDANCE["pending"])
    recent_follow_ups = _build_recent_follow_ups_digest(follow_ups, max_input_chars)
    return {
        "leadName": str(getattr(lead, "name", "客户") or "客户"),
        "leadStatus": status_key,
        "leadStatusLabel": status_label,
        "leadSource": str(getattr(lead, "source", "manual") or "manual"),
        "lastFollowUp": latest_content,
        "recentFollowUps": recent_follow_ups,
        "userGoal": goal,
        "sceneGuidance": scene_guidance,
    }


async def _call_ai_provider(
    *,
    context: dict[str, str],
    api_key: str,
    base_url: str,
    model: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    system_prompt = (
        "你是招商加盟业务的资深销售跟进教练。"
        "你的输出必须可直接用于下一次触达，强调加盟评估、政策沟通、到访转化和签约推进。"
        "请只输出JSON，不要markdown，不要额外解释。"
    )
    prompt = (
        "请基于以下CRM上下文，生成高可执行建议。\n"
        "输出要求:\n"
        "1) nextSentence: 1-2句，口语化，避免空话；\n"
        "2) nextAction: 必须包含明确动作和时间建议；\n"
        "3) riskPoints: 2-3条，聚焦丢单/降温风险；\n"
        "4) recommendedScript: 80-180字，适合直接发给客户；\n"
        "5) evidence: 2-4条，必须引用上下文客户信息；\n"
        "6) confidence: 0-1 小数。\n"
        "必须严格返回字段: nextSentence,nextAction,riskPoints,recommendedScript,confidence,evidence。\n"
        f"上下文: {json.dumps(context, ensure_ascii=False)}"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    url = f"{base_url.rstrip('/')}/chat/completions"

    def _do_request() -> dict[str, Any]:
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else ""
            raise AppException(f"AI服务调用失败: {detail or exc.reason}", business_code=400, status_code=502) from exc
        except urllib.error.URLError as exc:
            raise AppException("AI服务不可用，请稍后重试", business_code=400, status_code=502) from exc

        parsed = json.loads(raw)
        content = (
            parsed.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        json_payload = _extract_json_payload(str(content))
        return _validate_ai_suggestion_payload(json.loads(json_payload), fallback_model=model)

    return await asyncio.to_thread(_do_request)


async def generate_ai_follow_up_suggestion(
    session: AsyncSession,
    lead_id: str,
    *,
    current_staff: dict[str, Any],
    user_goal: str | None = None,
) -> dict[str, Any]:
    ai_config = await _resolve_ai_runtime_config(session)
    if not ai_config.enabled:
        raise AppException("AI能力暂未开启，请联系管理员开启", business_code=400, status_code=400)

    lead = await leads_repository.get_lead(session, lead_id)
    if lead is None:
        raise AppException("客户不存在", business_code=400, status_code=404)
    await _ensure_lead_access(session, lead, current_staff)

    follow_ups = await leads_repository.list_follow_ups(session, lead_id)
    context = _build_ai_context(
        lead,
        follow_ups,
        user_goal,
        max_input_chars=ai_config.max_input_chars,
    )
    start = time.perf_counter()
    try:
        if ai_config.api_key:
            data = await asyncio.wait_for(
                _call_ai_provider(
                    context=context,
                    api_key=ai_config.api_key,
                    base_url=ai_config.base_url,
                    model=ai_config.model,
                    timeout_seconds=ai_config.timeout_seconds,
                ),
                timeout=ai_config.timeout_seconds,
            )
            logger.info(
                "ai_suggestion_success lead_id=%s staff_id=%s duration_ms=%s model=%s",
                lead_id,
                str(current_staff.get("staffId") or ""),
                int((time.perf_counter() - start) * 1000),
                data.get("model"),
            )
            return data

        data = await asyncio.wait_for(
            _build_ai_suggestion_payload(
                lead,
                follow_ups,
                user_goal,
                ai_config.max_input_chars,
            ),
            timeout=ai_config.timeout_seconds,
        )
        logger.info(
            "ai_suggestion_fallback lead_id=%s staff_id=%s duration_ms=%s reason=no_api_key",
            lead_id,
            str(current_staff.get("staffId") or ""),
            int((time.perf_counter() - start) * 1000),
        )
        return data
    except asyncio.TimeoutError as exc:
        raise AppException("AI建议生成超时，请稍后重试", business_code=400, status_code=504) from exc
    except AppException:
        raise
    except Exception as exc:
        logger.exception("ai_suggestion_failed lead_id=%s", lead_id)
        raise AppException("AI建议生成失败，请稍后重试", business_code=400, status_code=502) from exc


async def assign_leads(
    session: AsyncSession,
    lead_ids: list[str],
    staff_id: str,
    current_staff: dict[str, Any],
) -> dict[str, Any]:
    target_staff = await leads_repository.get_user(session, staff_id)
    if target_staff is None:
        raise AppException("目标员工不存在", business_code=400, status_code=404)
    if target_staff.active is False:
        raise AppException("目标员工已停用", business_code=400, status_code=400)
    await _ensure_owner_assignment_permission(
        session,
        current_staff=current_staff,
        target_staff=target_staff,
    )

    assigned_ids: list[str] = []
    for lead_id in lead_ids:
        lead = await leads_repository.get_lead(session, lead_id)
        if lead is None:
            continue
        if lead.owner_id == staff_id:
            continue
        lead.owner_id = staff_id
        assigned_ids.append(lead_id)

    await leads_repository.commit(session)
    return {
        "leadIds": assigned_ids,
        "staffId": staff_id,
        "count": len(assigned_ids),
    }


async def transfer_leads_to_pool(
    session: AsyncSession,
    lead_ids: list[str],
    current_staff: dict[str, Any],
) -> dict[str, Any]:
    operator_staff_id = str(current_staff.get("staffId") or "system")
    operator_name = str(current_staff.get("name") or "当前员工")
    now = datetime.now(timezone.utc)
    transferred_ids: list[str] = []

    for lead_id in lead_ids:
        lead = await leads_repository.get_lead(session, lead_id)
        if lead is None:
            continue
        await _ensure_lead_access(session, lead, current_staff)
        if lead.owner_id is None:
            continue

        previous_owner_id = lead.owner_id
        previous_owner_name = previous_owner_id
        previous_owner = await leads_repository.get_user(session, previous_owner_id)
        if previous_owner is not None and previous_owner.name:
            previous_owner_name = previous_owner.name

        lead.owner_id = None
        dynamic_data = dict(lead.dynamic_data or {})
        dynamic_data.update(
            {
                "drop_reason_type": "手动转入公海",
                "drop_reason_detail": f"{operator_name}手动转入公海",
                "drop_time": now.isoformat(sep=" "),
                "original_owner": previous_owner_name,
            }
        )
        lead.dynamic_data = dynamic_data

        leads_repository.add_pool_transfer_log(
            session,
            PoolTransferLog(
                lead_id=lead.id,
                action="manual_drop",
                from_owner_id=previous_owner_id,
                to_owner_id=None,
                operator_staff_id=operator_staff_id,
        note="客户页手动转入公海",
            ),
        )
        transferred_ids.append(lead_id)

    await leads_repository.commit(session)
    return {
        "leadIds": transferred_ids,
        "count": len(transferred_ids),
    }


async def export_leads_csv(
    session: AsyncSession,
    *,
    keyword: str | None,
    status: str | None,
    source: str | None,
) -> bytes:
    base_query = leads_repository.build_leads_query(
        keyword,
        status,
        source,
        exclude_pool=True,
    )
    leads = await leads_repository.list_leads(session, base_query, page=1, page_size=100000)
    custom_fields = await settings_repository.list_custom_fields(session, "lead")
    export_custom_fields = [
        field
        for field in custom_fields
        if field.active and (not field.is_system) and field.code not in _BASE_EXPORT_FIELD_CODES
    ]
    owner_name_map: dict[str, str] = {}
    follow_up_operator_name_map: dict[str, str] = {}
    for lead in leads:
        if not lead.owner_id or lead.owner_id in owner_name_map:
            continue
        owner = await leads_repository.get_user(session, lead.owner_id)
        owner_name_map[lead.owner_id] = owner.name if owner and owner.name else lead.owner_id

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "客户姓名",
        "手机号码",
        "来源渠道",
        "跟进状态",
        "意向评级",
        "归属销售",
        "客户标签",
        "最后跟进时间",
        "跟进记录",
        "跟进方式",
        "跟进人",
        "跟进时间",
        "扩展字段JSON",
    ] + [field.name for field in export_custom_fields])
    for lead in leads:
        follow_ups = await leads_repository.list_follow_ups(session, lead.id)
        latest_follow_up = follow_ups[0] if follow_ups else None
        follow_up_operator_name = ""
        if latest_follow_up is not None:
            raw_operator = str(latest_follow_up.operator or "").strip()
            if raw_operator:
                if raw_operator in follow_up_operator_name_map:
                    follow_up_operator_name = follow_up_operator_name_map[raw_operator]
                else:
                    mapped_name = raw_operator
                    user = await leads_repository.get_user(session, raw_operator)
                    if user is not None and user.name:
                        mapped_name = user.name
                    follow_up_operator_name_map[raw_operator] = mapped_name
                    follow_up_operator_name = mapped_name
        custom_values: list[str] = []
        for field in export_custom_fields:
            raw_value = (lead.dynamic_data or {}).get(field.code)
            if raw_value is None:
                custom_values.append("")
            elif isinstance(raw_value, list):
                custom_values.append("|".join(str(item) for item in raw_value))
            elif isinstance(raw_value, dict):
                custom_values.append(json.dumps(raw_value, ensure_ascii=False))
            else:
                custom_values.append(str(raw_value))

        writer.writerow([
            lead.name,
            lead.phone,
            _SOURCE_EXPORT_LABELS.get(lead.source, lead.source),
            _STATUS_EXPORT_LABELS.get(lead.status, lead.status),
            lead.level,
            owner_name_map.get(lead.owner_id or "", ""),
            "|".join(lead.tags or []),
            lead.last_follow_up.isoformat(sep=" ") if lead.last_follow_up else "",
            latest_follow_up.content if latest_follow_up else "",
            latest_follow_up.type if latest_follow_up else "",
            follow_up_operator_name,
            latest_follow_up.timestamp.isoformat(sep=" ") if latest_follow_up else "",
            json.dumps(lead.dynamic_data or {}, ensure_ascii=False),
        ] + custom_values)
    return output.getvalue().encode("utf-8-sig")


async def import_leads_csv(
    session: AsyncSession,
    *,
    csv_content: str,
    current_staff: dict[str, Any],
) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(csv_content))
    if not reader.fieldnames:
        raise AppException("导入文件为空或格式错误", business_code=400, status_code=400)

    required_fields = {
        "name": "客户姓名",
        "phone": "手机号码",
        "source": "来源渠道",
    }
    missing_labels: list[str] = []
    for field_key, label in required_fields.items():
        aliases = _HEADER_ALIASES[field_key]
        if not any(alias in reader.fieldnames for alias in aliases):
            missing_labels.append(label)
    if missing_labels:
        raise AppException(f"导入模板缺少字段: {', '.join(missing_labels)}", business_code=400, status_code=400)

    total = 0
    success = 0
    errors: list[str] = []
    for index, row in enumerate(reader, start=2):
        if not any((value or "").strip() for value in row.values()):
            continue
        total += 1
        try:
            name = _field_value(row, "name")
            phone = _field_value(row, "phone")
            source = _normalize_source(_field_value(row, "source"))
            project = _field_value(row, "project") or "默认项目"
            status = _normalize_status(_field_value(row, "status"))
            level = _normalize_level(_field_value(row, "level"))
            owner = _field_value(row, "owner") or None

            if not name or not phone or not source:
                raise AppException("必填字段缺失: 客户姓名/手机号码/来源渠道", business_code=400, status_code=400)

            tags_raw = _field_value(row, "tags")
            tags = [item.strip() for item in tags_raw.split("|") if item.strip()] if tags_raw else []
            last_follow_up = _parse_datetime(_field_value(row, "last_follow_up"))

            dynamic_data_raw = _field_value(row, "dynamic_data")
            dynamic_data: dict[str, Any] = {}
            if dynamic_data_raw:
                parsed = json.loads(dynamic_data_raw)
                if isinstance(parsed, dict):
                    dynamic_data = parsed

            payload = LeadCreate.model_validate(
                {
                    "name": name,
                    "phone": phone,
                    "project": project,
                    "source": source,
                    "status": status,
                    "level": level,
                    "owner": owner,
                    "tags": tags,
                    "lastFollowUp": last_follow_up,
                    "dynamicData": dynamic_data,
                }
            )
            lead_data = await create_lead(session, payload, current_staff)

            follow_up_content = _field_value(row, "follow_up_content")
            if follow_up_content:
                follow_up_type = _field_value(row, "follow_up_type") or "call"
                follow_up_operator = _field_value(row, "follow_up_operator") or str(current_staff.get("name") or "导入员")
                follow_up_time = _parse_datetime(_field_value(row, "follow_up_time")) or last_follow_up
                follow_up_payload = FollowUpCreate(
                    type=follow_up_type,
                    content=follow_up_content,
                    operator=follow_up_operator,
                    timestamp=follow_up_time,
                )
                await create_follow_up(session, str(lead_data["id"]), follow_up_payload, current_staff)
            success += 1
        except Exception as exc:
            errors.append(f"第{index}行导入失败: {str(exc)}")

    return {
        "total": total,
        "success": success,
        "failed": total - success,
        "errors": errors[:20],
    }


async def list_assignable_staff(session: AsyncSession, current_staff: dict[str, Any]) -> dict[str, Any]:
    role = normalize_role(str(current_staff.get("role") or ""))
    if role == "admin":
        users = await leads_repository.list_active_users(session)
    elif role == "manager":
        actor = await _get_actor_user(session, current_staff)
        if actor is None or not actor.dept_name:
            return {"list": []}
        users = await leads_repository.list_active_users_by_department(session, actor.dept_name)
    else:
        raise AppException("无权限执行该操作", business_code=401, status_code=403)

    return {
        "list": [_to_assignable_staff_dict(user) for user in users],
    }
async def _get_actor_user(session: AsyncSession, current_staff: dict[str, Any]) -> User | None:
    staff_id = str(current_staff.get("staffId") or "").strip()
    if not staff_id:
        return None
    return await leads_repository.get_user(session, staff_id)


async def _ensure_owner_assignment_permission(
    session: AsyncSession,
    *,
    current_staff: dict[str, Any],
    target_staff: Any,
) -> None:
    actor_role = normalize_role(str(current_staff.get("role") or ""))
    if actor_role == "admin":
        return
    if actor_role != "manager":
        raise AppException("无权限分配客户", business_code=401, status_code=403)

    actor = await _get_actor_user(session, current_staff)
    if actor is None or not actor.dept_name:
        raise AppException("主管未绑定所属部门，无法改派", business_code=400, status_code=400)
    if actor.dept_name != target_staff.dept_name:
        raise AppException("主管仅可改派本部门员工", business_code=400, status_code=403)


def _to_assignable_staff_dict(user: Any) -> dict[str, Any]:
    return {
        "id": user.id,
        "name": user.name,
        "deptName": user.dept_name,
    }


async def _ensure_lead_access(
    session: AsyncSession,
    lead: Lead,
    current_staff: dict[str, Any] | None,
) -> None:
    if current_staff is None:
        return
    role = normalize_role(str(current_staff.get("role") or ""))
    if role == "admin":
        return

    actor_staff_id = str(current_staff.get("staffId") or "")
    if role == "sales":
        if lead.owner_id != actor_staff_id:
            raise AppException("无权限访问该客户", business_code=401, status_code=403)
        return

    if role == "manager":
        actor = await _get_actor_user(session, current_staff)
        if actor is None or not actor.dept_name:
            raise AppException("主管未绑定所属部门", business_code=400, status_code=403)
        if not lead.owner_id:
            raise AppException("无权限访问该客户", business_code=401, status_code=403)
        owner = await leads_repository.get_user(session, lead.owner_id)
        if owner is None or owner.dept_name != actor.dept_name:
            raise AppException("无权限访问该客户", business_code=401, status_code=403)
        return

        raise AppException("无权限访问该客户", business_code=401, status_code=403)
