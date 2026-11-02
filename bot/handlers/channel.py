import asyncio
import html
import logging
import random

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import BadRequest, FloodWait, MessageNotModified

from bot.core.caption import build_caption
from bot.core.buttons import parse_buttons
from bot.core.dispatcher import dispatcher
from bot.database import db
from bot.ui.markup import to_markup

log = logging.getLogger("channel")

# টেলিগ্রামের স্ট্যান্ডার্ড ভ্যালিড রিঅ্যাকশন ইমোজি লিস্ট
REACTIONS = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "⚡", "💯", "🏆", "😍", "🤗", "👌", "😎"]
MEDIA = filters.document | filters.video | filters.audio | filters.animation


async def retry(fn, *a, **kw):
    for _ in range(4):
        try:
            return await fn(*a, **kw)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
        except Exception as e:
            log.warning("Operation failed: %s", e)
            break
    return None


async def process(c: Client, m):
    chat_id = m.chat.id
    if chat_id not in db.known:
        await db.add_channel(chat_id, m.chat.title or str(chat_id))
    s = await db.get_settings(chat_id)
    if not s["enabled"]:
        return

    media = m.document or m.video or m.audio or m.animation
    filename = getattr(media, "file_name", None) or getattr(media, "title", None) or ""
    caption = build_caption(
        s, filename, getattr(media, "file_size", 0), getattr(media, "duration", 0),
        m.caption.html if m.caption else "", m.caption or "")
    markup = to_markup(parse_buttons(s["buttons"]))

    try:
        await retry(m.edit_caption, caption, reply_markup=markup)
    except MessageNotModified:
        pass
    except BadRequest:
        try:
            await retry(m.edit_caption, f"<b>{html.escape(filename)[:900]}</b>", reply_markup=markup)
        except Exception:
            log.warning("edit failed in %s", chat_id)
    except Exception as e:
        log.warning("edit failed in %s: %s", chat_id, e)

    # রিঅ্যাকশন পাঠানো: সরাসরি m.react() মেথড ব্যবহার করা হয়েছে
    if s.get("react"):
        try:
            emoji = random.choice(REACTIONS)
            await m.react(emoji)
        except Exception as e:
            log.warning("Reaction failed in %s: %s (Make sure reactions are enabled in channel settings)", chat_id, e)

    if s.get("sticker"):
        try:
            await retry(c.send_sticker, chat_id, s["sticker"])
        except Exception as e:
            log.warning("Sticker send failed in %s: %s", chat_id, e)

    db.incr(chat_id)


@Client.on_message(filters.channel & MEDIA, group=1)
async def on_media(c: Client, m):
    dispatcher.submit(m.chat.id, process, c, m)


@Client.on_chat_member_updated()
async def on_membership(c: Client, u):
    if not u.chat or u.chat.type.name != "CHANNEL":
        return
    new, old = u.new_chat_member, u.old_chat_member
    if new and new.user and new.user.is_self and new.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        await db.add_channel(u.chat.id, u.chat.title, u.from_user.id if u.from_user else None)
    elif old and old.user and old.user.is_self and (not new or new.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED)):
        await db.remove_channel(u.chat.id)

        
