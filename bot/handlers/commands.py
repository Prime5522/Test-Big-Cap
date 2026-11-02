"""Channel commands – every command is deleted right after use and answered with a self-destructing note."""
import asyncio
import html
import re

from pyrogram import Client, filters

from bot.core.buttons import parse_buttons
from bot.core.caption import build_caption
from bot.database import db
from bot.ui import texts as T
from bot.ui.markup import to_markup

SAMPLE = "Avengers.Endgame.2019.1080p.BluRay.x265.Hindi.English.ESub.mkv"
FIELDS = ("audio", "quality", "year")


def _split(arg: str) -> list[str]:
    return [x.strip() for x in arg.split("|") if x.strip()]


def _merge(old: list, new: list, key=lambda x: str(x).lower()) -> list:
    seen, out = set(), []
    for item in [*old, *new]:
        if key(item) not in seen:
            seen.add(key(item))
            out.append(item)
    return out


def _pairs(arg: str) -> list[list[str]]:
    out = []
    for part in _split(arg):
        old, sep, new = part.partition(":")
        if sep and old.strip():
            out.append([old.strip(), new.strip()])
    return out


# ── handlers: (client, message, arg) → reply text | (text, ttl) ───────────────
async def setcap(c, m, arg):
    if not arg:
        return "⚠️ Usage: <code>/setcap your text {name}</code>"
    await db.update_settings(m.chat.id, caption=arg)
    return "✅ Custom caption saved."

async def delcap(c, m, arg):
    await db.update_settings(m.chat.id, caption=None)
    return "🗑 Custom caption removed – default caption restored."

async def prefix(c, m, arg):
    if not arg:
        return "⚠️ Usage: <code>/prefix text</code>"
    await db.update_settings(m.chat.id, prefix=arg)
    return "✅ Prefix saved."

async def prefixoff(c, m, arg):
    await db.update_settings(m.chat.id, prefix="")
    return "✅ Prefix removed."

async def suffix(c, m, arg):
    if not arg:
        return "⚠️ Usage: <code>/suffix text</code>"
    await db.update_settings(m.chat.id, suffix=arg)
    return "✅ Suffix saved."

async def suffixoff(c, m, arg):
    await db.update_settings(m.chat.id, suffix="")
    return "✅ Suffix removed."

async def btns(c, m, arg):
    rows = parse_buttons(arg)
    if not rows:
        return "⚠️ Usage: <code>/btns [Text](https://link)</code>\nSee Help → Buttons."
    await db.update_settings(m.chat.id, buttons=arg)
    return f"✅ {sum(map(len, rows))} button(s) saved in {len(rows)} row(s)."

async def btnsoff(c, m, arg):
    await db.update_settings(m.chat.id, buttons="")
    return "✅ Buttons removed."

async def react(c, m, arg):
    await db.update_settings(m.chat.id, react=True)
    return "✅ Auto reactions enabled."

async def reactoff(c, m, arg):
    await db.update_settings(m.chat.id, react=False)
    return "✅ Auto reactions disabled."

async def setsticker(c, m, arg):
    st = m.reply_to_message.sticker if m.reply_to_message else None
    if not st:
        return "⚠️ Reply to a sticker with <code>/setsticker</code>."
    await db.update_settings(m.chat.id, sticker=st.file_id)
    return "✅ Sticker saved."

async def clearsticker(c, m, arg):
    await db.update_settings(m.chat.id, sticker=None)
    return "✅ Sticker removed."

async def autoclean(c, m, arg):
    await db.update_settings(m.chat.id, autoclean=True)
    return "✅ Auto clean enabled."

async def autocleanoff(c, m, arg):
    await db.update_settings(m.chat.id, autoclean=False)
    return "✅ Auto clean disabled."

async def remwords(c, m, arg):
    append = arg.startswith("+")
    words = _split(arg[1:] if append else arg)
    if not words:
        return "⚠️ Usage: <code>/remwords word1|word2</code>"
    cur = (await db.get_settings(m.chat.id))["remove"] if append else []
    await db.update_settings(m.chat.id, remove=_merge(cur, words))
    return f"✅ {len(words)} word(s) will be removed."

async def remwordsoff(c, m, arg):
    await db.update_settings(m.chat.id, remove=[])
    return "✅ Remove rules cleared."

async def replace(c, m, arg):
    append = arg.startswith("+")
    pairs = _pairs(arg[1:] if append else arg)
    if not pairs:
        return "⚠️ Usage: <code>/replace old:new|old2:new2</code>"
    cur = (await db.get_settings(m.chat.id))["replace"] if append else []
    await db.update_settings(m.chat.id, replace=_merge(cur, pairs, key=lambda p: p[0].lower()))
    return f"✅ {len(pairs)} replace rule(s) saved."

async def replaceoff(c, m, arg):
    await db.update_settings(m.chat.id, replace=[])
    return "✅ Replace rules cleared."

async def hashtag(c, m, arg):
    fields = [f for f in dict.fromkeys(re.split(r"[|,\s]+", arg.lower())) if f in FIELDS]
    if not fields:
        return "⚠️ Usage: <code>/hashtag audio|quality|year</code>"
    await db.update_settings(m.chat.id, hashtags=fields)
    return "✅ Hashtags enabled for: " + ", ".join(fields)

async def showhashtag(c, m, arg):
    f = (await db.get_settings(m.chat.id))["hashtags"]
    return "# Hashtag fields: " + (", ".join(f) if f else "none")

async def clearhashtag(c, m, arg):
    await db.update_settings(m.chat.id, hashtags=[])
    return "✅ Hashtags disabled."

async def pause(c, m, arg):
    await db.update_settings(m.chat.id, enabled=False)
    return "⏸ Bot paused in this channel. Use /resume to continue."

async def resume(c, m, arg):
    await db.update_settings(m.chat.id, enabled=True)
    return "▶️ Bot resumed."

async def reset(c, m, arg):
    await db.reset_settings(m.chat.id)
    return "♻️ All settings were reset to default."

async def getkey(c, m, arg):
    key = await db.create_key(m.chat.id)
    return (f"🔑 <b>Settings key</b>\n<code>{key}</code>\n\nSend <code>/apply {key}</code> in the target channel.\n"
            "One-time • expires in 10 min • this message self-deletes in 30 s", 30)

async def apply(c, m, arg):
    if not arg:
        return "⚠️ Usage: <code>/apply KEY</code>"
    src = await db.consume_key(arg.strip())
    if not src:
        return "❌ Invalid, used or expired key."
    if src == m.chat.id:
        return "⚠️ Key was created in this same channel."
    await db.copy_settings(src, m.chat.id)
    return "✅ Settings copied successfully."

async def details(c, m, arg):
    s = await db.get_settings(m.chat.id)
    short = lambda t: html.escape(t if len(t) < 70 else t[:67] + "…") if t else "—"
    text = (
        "<blockquote><b>📄 Channel Config</b></blockquote>\n"
        f"{'🟢 Active' if s['enabled'] else '⏸ Paused'}\n\n"
        f"📝 <b>Caption:</b> {'custom' if s['caption'] else 'default'}\n"
        f"🔤 <b>Prefix:</b> {short(s['prefix'])}\n🔚 <b>Suffix:</b> {short(s['suffix'])}\n"
        f"🔘 <b>Buttons:</b> {sum(map(len, parse_buttons(s['buttons'])))}\n"
        f"🎭 <b>Reactions:</b> {'on' if s['react'] else 'off'}\n🎉 <b>Sticker:</b> {'set' if s['sticker'] else '—'}\n"
        f"🪄 <b>AutoClean:</b> {'on' if s['autoclean'] else 'off'}\n"
        f"# <b>Hashtags:</b> {', '.join(s['hashtags']) or '—'}\n"
        f"❌ <b>Remove:</b> {short(', '.join(s['remove']))}\n"
        f"🔁 <b>Replace:</b> {len(s['replace'])} rule(s)"
    )
    return text, 30

async def preview(c, m, arg):
    s = await db.get_settings(m.chat.id)
    text = build_caption(s, SAMPLE, 2470000000, 6700, "Original caption sample", "Original caption sample")
    return "<b>👁 Preview</b> (sample file)\n\n" + text, 30, to_markup(parse_buttons(s["buttons"]))


HANDLERS = {f.__name__: f for f in (
    setcap, delcap, prefix, prefixoff, suffix, suffixoff, btns, btnsoff, react, reactoff, setsticker,
    clearsticker, autoclean, autocleanoff, remwords, remwordsoff, replace, replaceoff, hashtag,
    showhashtag, clearhashtag, pause, resume, reset, getkey, apply, details, preview)}


async def _delete_later(msg, ttl: int):
    await asyncio.sleep(ttl)
    try:
        await msg.delete()
    except Exception:
        pass


@Client.on_message(filters.channel & filters.command(list(HANDLERS)), group=2)
async def channel_command(c: Client, m):
    name = m.command[0].lower()
    parts = (m.text or "").split(None, 1)
    arg = parts[1].strip() if len(parts) > 1 else ""
    try:
        await m.delete()                       # keeps the channel clean (and hides keys)
    except Exception:
        pass
    if m.chat.id not in db.known:
        await db.add_channel(m.chat.id, m.chat.title or str(m.chat.id))

    result = await HANDLERS[name](c, m, arg)
    text, ttl, markup = (result, 6, None) if isinstance(result, str) else (*result, None)[:3]
    msg = await c.send_message(m.chat.id, text, reply_markup=markup)
    asyncio.create_task(_delete_later(msg, ttl))


@Client.on_message(filters.private & filters.command(list(HANDLERS)), group=2)
async def private_hint(c: Client, m):
    await m.reply_text(T.PRIVATE_HINT)
