import aioredis
import json
import logging
from typing import Optional
from app.core.config import settings


class RedisClient:
    """Simple Redis wrapper with an in-memory fallback for local development/tests."""

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._local_store = {}

    async def connect(self):
        try:
            self._client = aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
            # try a ping
            await self._client.ping()
            logging.info("Connected to Redis at %s", settings.REDIS_URL)
        except Exception:
            logging.exception("Could not connect to Redis, falling back to in-memory store")
            self._client = None

    async def close(self):
        try:
            if self._client:
                await self._client.close()
        except Exception:
            pass

    async def set_context(self, session_id: str, context: list, ttl: Optional[int] = None):
        key = f"session:{session_id}:context"
        val = json.dumps(context, ensure_ascii=False)
        if self._client:
            await self._client.set(key, val, ex=ttl or settings.REDIS_TTL)
        else:
            # fallback
            self._local_store[key] = val

    async def get_context(self, session_id: str):
        key = f"session:{session_id}:context"
        if self._client:
            v = await self._client.get(key)
            return json.loads(v) if v else None
        else:
            v = self._local_store.get(key)
            return json.loads(v) if v else None


redis_client = RedisClient()
