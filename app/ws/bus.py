import asyncio
import importlib
from collections.abc import AsyncIterator
from typing import Any, Protocol

from app.core.config import settings


class MessageBus(Protocol):
    async def publish(self, channel: str, message: str) -> None: ...

    def subscribe(self, channel: str) -> AsyncIterator[str]: ...

    def publish_nowait(self, channel: str, message: str) -> None: ...


class InMemoryMessageBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[str]]] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def publish(self, channel: str, message: str) -> None:
        async with self._lock:
            queues = list(self._subscribers.get(channel, set()))
        for queue in queues:
            queue.put_nowait(message)

    def publish_nowait(self, channel: str, message: str) -> None:
        queues = list(self._subscribers.get(channel, set()))
        for queue in queues:
            queue.put_nowait(message)

    async def subscribe(self, channel: str) -> AsyncIterator[str]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        async with self._lock:
            self._subscribers.setdefault(channel, set()).add(queue)

        try:
            while True:
                yield await queue.get()
        finally:
            async with self._lock:
                subscribers = self._subscribers.get(channel)
                if subscribers and queue in subscribers:
                    subscribers.remove(queue)
                if subscribers is not None and not subscribers:
                    _ = self._subscribers.pop(channel, None)


class RedisMessageBus:
    def __init__(self, redis_url: str) -> None:
        self._redis_url: str = redis_url
        self._redis: Any = None

    async def _get_redis(self):
        if self._redis is None:
            redis_module = importlib.import_module("redis.asyncio")
            self._redis = redis_module.Redis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def publish(self, channel: str, message: str) -> None:
        redis = await self._get_redis()
        await redis.publish(channel, message)

    def publish_nowait(self, channel: str, message: str) -> None:
        try:
            loop = asyncio.get_running_loop()
            _ = loop.create_task(self.publish(channel, message))
        except RuntimeError:
            pass

    async def subscribe(self, channel: str) -> AsyncIterator[str]:
        redis = await self._get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)

        try:
            while True:
                item = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if item and isinstance(item.get("data"), str):
                    yield item["data"]
                await asyncio.sleep(0.05)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()


_message_bus: MessageBus | None = None


def get_message_bus() -> MessageBus:
    global _message_bus
    if _message_bus is None:
        if settings.message_bus_backend.lower() == "redis":
            _message_bus = RedisMessageBus(settings.redis_url)
        else:
            _message_bus = InMemoryMessageBus()
    return _message_bus


def build_voice_assist_channel(staff_id: str) -> str:
    return f"{settings.ws_voice_assist_channel_prefix}:{staff_id}"
