import asyncio
import contextlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.dependencies import get_current_staff, require_admin
from app.core.exceptions import AppException
from app.core.response import success_response
from app.core.security import decode_access_token
from app.schemas.common import ApiEnvelope
from app.schemas.ws import VoiceAssistPublishData, VoiceAssistPublishRequest
from app.ws.bus import build_voice_assist_channel, get_message_bus

router = APIRouter(prefix="/ws", tags=["ws"])
logger = logging.getLogger(__name__)
WS_SCHEMA_VERSION = "1.0"


def _normalize_event(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {"type": "ai_hint", "content": str(payload)}
    payload.setdefault("version", WS_SCHEMA_VERSION)
    payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    return payload


async def _publish_with_retry(bus: Any, channel: str, event: dict[str, Any], max_retry: int = 3) -> None:
    raw = json.dumps(event, ensure_ascii=False)
    for attempt in range(1, max_retry + 1):
        try:
            await bus.publish(channel, raw)
            return
        except Exception as exc:
            logger.warning("WS publish failed attempt=%s channel=%s error=%s", attempt, channel, str(exc))
            if attempt == max_retry:
                raise AppException("消息发布失败", business_code=400, status_code=500) from exc
            await asyncio.sleep(0.1 * attempt)


@router.post("/voice-assist/{staff_id}/publish", response_model=ApiEnvelope[VoiceAssistPublishData])
async def publish_voice_assist_event(
    staff_id: str,
    payload: VoiceAssistPublishRequest,
    _: dict[str, Any] = Depends(require_admin),
    current_staff: dict[str, Any] = Depends(get_current_staff),
) -> dict[str, Any]:
    channel = build_voice_assist_channel(staff_id)
    bus = get_message_bus()
    event = _normalize_event(
        {
            "type": payload.type,
            "content": payload.content,
            "source": "api",
            "operatorStaffId": current_staff.get("staffId", "system"),
        }
    )
    await _publish_with_retry(bus, channel, event)
    data = {
        "channel": channel,
        "staffId": staff_id,
        "eventType": payload.type,
        "version": WS_SCHEMA_VERSION,
    }
    return success_response(data=data, message="消息已发布")


@router.websocket("/voice-assist/{staff_id}")
async def voice_assist_ws(websocket: WebSocket, staff_id: str, token: str | None = Query(default=None)) -> None:
    verified_staff_id = staff_id
    if settings.auth_enabled:
        if not token:
            await websocket.close(code=1008, reason="missing token")
            return
        payload = decode_access_token(token)
        token_staff_id = str(payload.get("staffId"))
        if token_staff_id != staff_id:
            await websocket.close(code=1008, reason="staff mismatch")
            return
        verified_staff_id = token_staff_id

    bus = get_message_bus()
    channel = build_voice_assist_channel(verified_staff_id)

    await websocket.accept()
    await websocket.send_json(
        {
            "type": "connected",
            "staffId": verified_staff_id,
            "channel": channel,
            "version": WS_SCHEMA_VERSION,
        }
    )

    async def relay_bus_messages() -> None:
        async for raw_message in bus.subscribe(channel):
            try:
                payload = json.loads(raw_message)
            except json.JSONDecodeError:
                payload = {"type": "ai_hint", "content": raw_message}
            await websocket.send_json(_normalize_event(payload))

    relay_task = asyncio.create_task(relay_bus_messages())
    await asyncio.sleep(0)

    try:
        while True:
            incoming_text = await websocket.receive_text()
            try:
                client_event = json.loads(incoming_text)
            except json.JSONDecodeError:
                client_event = {"type": "raw", "content": incoming_text}

            event_type = client_event.get("type") if isinstance(client_event, dict) else None
            if event_type == "ping":
                await websocket.send_json(
                    _normalize_event({"type": "pong", "staffId": verified_staff_id})
                )
            elif event_type == "publish_test":
                content = client_event.get("content", "test message")
                await _publish_with_retry(
                    bus,
                    channel,
                    _normalize_event({"type": "ai_hint", "content": content, "source": "ws_test"}),
                )
    except WebSocketDisconnect:
        pass
    finally:
        relay_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await relay_task
