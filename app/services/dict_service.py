from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import dict_repository

DICT_TYPE_ALIASES: dict[str, str] = {
    "status": "lead_status",
    "source": "lead_source",
    "level": "lead_level",
    "tag": "lead_tag",
    "tags": "lead_tag",
    "loss_reason": "loss_reason",
}

FALLBACK_DICTS: dict[str, list[dict[str, str]]] = {
    "lead_status": [
        {"value": "pending", "label": "待跟进"},
        {"value": "communicating", "label": "初步沟通"},
        {"value": "deep_following", "label": "深度跟进"},
        {"value": "invited", "label": "已邀约"},
        {"value": "visited", "label": "已到访"},
        {"value": "deposit_paid", "label": "已交定金"},
        {"value": "signed", "label": "已签约"},
    {"value": "invalid", "label": "无效客户"},
        {"value": "lost", "label": "战败流失"},
    ],
    "lead_source": [
        {"value": "douyin", "label": "抖音广告"},
        {"value": "baidu", "label": "百度搜索"},
        {"value": "expo", "label": "线下展会"},
        {"value": "referral", "label": "转介绍"},
    ],
    "lead_tag": [
        {"value": "high_value", "label": "高净值"},
        {"value": "franchise_exp", "label": "曾加盟过"},
        {"value": "mall_shop", "label": "商场铺"},
        {"value": "competitor_convert", "label": "竞品转出"},
        {"value": "signed", "label": "已签约"},
    ],
}


def _normalize_dict_type(dict_type: str) -> str:
    return DICT_TYPE_ALIASES.get(dict_type, dict_type)


def _deduplicate_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        value = item.get("value")
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(item)
    return deduped


async def get_dict_items(session: AsyncSession, dict_type: str) -> list[dict[str, str]]:
    normalized_dict_type = _normalize_dict_type(dict_type)
    stmt = dict_repository.build_dict_query(normalized_dict_type)
    items = await dict_repository.list_dict_items(session, stmt)
    if not items:
        return _deduplicate_items(FALLBACK_DICTS.get(normalized_dict_type, []))

    return _deduplicate_items([{"value": item.item_key, "label": item.item_label} for item in items])
