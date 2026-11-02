import asyncio

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked

from bot.database import db
from config import Config

ADMIN = filters.private & filters.user(Config.ADMINS or [0])


@Client.on_message(ADMIN & filters.command("stats"))
async def stats(c, m):
    s = await db.stats()
    await m.reply_text(f"📊 <b>Stats</b>\n\n👤 Users: {s['users']}\n📢 Channels: {s['channels']}\n✅ Files: {s['files']}")


@Client.on_message(ADMIN & filters.command("broadcast") & filters.reply)
async def broadcast(c, m):
    status = await m.reply_text("📣 Broadcasting…")
    asyncio.create_task(_run(m.reply_to_message, status))


async def _run(src, status):
    ok = fail = 0
    async for u in db.users.find({}, {"_id": 1}):
        try:
            await src.copy(u["_id"])
            ok += 1
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
        except (UserIsBlocked, InputUserDeactivated):
            await db.users.delete_one({"_id": u["_id"]})
            fail += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.04)           # ~25 msg/s, safely under limits
    await status.edit_text(f"✅ Broadcast finished\n\nDelivered: {ok}\nFailed/removed: {fail}")
