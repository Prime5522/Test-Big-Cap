import asyncio
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

from config import Config

log = logging.getLogger("db")

DEFAULTS = {
    "enabled": True,
    "caption": None,
    "prefix": "",
    "suffix": "",
    "buttons": "",
    "react": False,
    "sticker": None,
    "autoclean": False,
    "remove": [],
    "replace": [],      # [[old, new], ...]
    "hashtags": [],     # subset of audio / quality / year
}


class Database:
    def __init__(self):
        self._client = AsyncIOMotorClient(Config.MONGO_URI, maxPoolSize=50, serverSelectionTimeoutMS=8000)
        d = self._client[Config.DB_NAME]
        self.users, self.channels, self.keys, self.meta = d.users, d.channels, d.keys, d.meta
        self._cache: dict[int, tuple[float, dict]] = {}
        self._pending: dict[int, int] = {}
        self.known: set[int] = set()
        self._task = None

    # ── lifecycle ────────────────────────────────────────────────
    async def init(self):
        await self.keys.create_index("expires_at", expireAfterSeconds=0)
        await self.channels.create_index("admins")
        self.known = {c["_id"] async for c in self.channels.find({}, {"_id": 1})}
        self._task = asyncio.create_task(self._flusher())
        log.info("database ready – %d channels", len(self.known))

    async def close(self):
        if self._task:
            self._task.cancel()
        await self._flush()
        self._client.close()

    # ── settings (RAM-cached) ────────────────────────────────────
    async def get_settings(self, chat_id: int) -> dict:
        now = time.monotonic()
        hit = self._cache.get(chat_id)
        if hit and hit[0] > now:
            return hit[1]
        doc = await self.channels.find_one({"_id": chat_id}, {"settings": 1}) or {}
        s = {**DEFAULTS, **(doc.get("settings") or {})}
        self._cache[chat_id] = (now + Config.SETTINGS_CACHE_TTL, s)
        return s

    async def update_settings(self, chat_id: int, **fields):
        if not fields:
            return
        await self.channels.update_one(
            {"_id": chat_id}, {"$set": {f"settings.{k}": v for k, v in fields.items()}}, upsert=True)
        self.known.add(chat_id)
        self._cache.pop(chat_id, None)

    async def reset_settings(self, chat_id: int):
        await self.channels.update_one({"_id": chat_id}, {"$set": {"settings": {}}})
        self._cache.pop(chat_id, None)

    async def copy_settings(self, src: int, dst: int):
        s = await self.get_settings(src)
        await self.channels.update_one({"_id": dst}, {"$set": {"settings": dict(s)}}, upsert=True)
        self._cache.pop(dst, None)

    # ── channels ─────────────────────────────────────────────────
    async def add_channel(self, chat_id: int, title: str, owner_id: int | None = None):
        upd = {"$set": {"title": title}, "$setOnInsert": {"added_at": datetime.now(timezone.utc), "files": 0}}
        if owner_id:
            upd["$addToSet"] = {"admins": owner_id}
        await self.channels.update_one({"_id": chat_id}, upd, upsert=True)
        self.known.add(chat_id)

    async def remove_channel(self, chat_id: int):
        await self.channels.delete_one({"_id": chat_id})
        self.known.discard(chat_id)
        self._cache.pop(chat_id, None)

    async def channel(self, chat_id: int):
        return await self.channels.find_one({"_id": chat_id})

    async def channels_for(self, user_id: int) -> list[dict]:
        return await self.channels.find({"admins": user_id}).sort("title", 1).to_list(200)

    # ── users ────────────────────────────────────────────────────
    async def add_user(self, user_id: int, name: str):
        await self.users.update_one(
            {"_id": user_id}, {"$set": {"name": name}, "$setOnInsert": {"joined": datetime.now(timezone.utc)}},
            upsert=True)

    # ── copy-settings keys ───────────────────────────────────────
    async def create_key(self, source: int) -> str:
        key = secrets.token_urlsafe(9)
        exp = datetime.now(timezone.utc) + timedelta(minutes=Config.KEY_TTL_MINUTES)
        await self.keys.insert_one({"_id": key, "source": source, "expires_at": exp})
        return key

    async def consume_key(self, key: str) -> int | None:
        doc = await self.keys.find_one_and_delete({"_id": key})
        if not doc:
            return None
        exp = doc["expires_at"]
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return doc["source"] if exp > datetime.now(timezone.utc) else None

    # ── buffered counters (one write per 5 s instead of one per file) ──
    def incr(self, chat_id: int):
        self._pending[chat_id] = self._pending.get(chat_id, 0) + 1

    async def _flush(self):
        if not self._pending:
            return
        batch, self._pending = self._pending, {}
        try:
            ops = [UpdateOne({"_id": cid}, {"$inc": {"files": n}}) for cid, n in batch.items()]
            await self.channels.bulk_write(ops, ordered=False)
            await self.meta.update_one({"_id": "stats"}, {"$inc": {"files": sum(batch.values())}}, upsert=True)
        except Exception:
            log.exception("counter flush failed")

    async def _flusher(self):
        while True:
            await asyncio.sleep(5)
            await self._flush()

    async def stats(self) -> dict:
        users = await self.users.estimated_document_count()
        channels = await self.channels.estimated_document_count()
        meta = await self.meta.find_one({"_id": "stats"}) or {}
        return {"users": users, "channels": channels, "files": meta.get("files", 0) + sum(self._pending.values())}


db = Database()
