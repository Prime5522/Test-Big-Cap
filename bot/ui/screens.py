from pyrogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M, WebAppInfo

from bot.database import db
from config import Config

from . import texts as T

# key → (text, rows of (label, callback), back target)
PAGES: dict[str, tuple[str, list[list[tuple[str, str]]], str]] = {
    "help": (T.HELP, [
        [("🎭 Reactions", "reactions"), ("🔘 Buttons", "buttons")],
        [("🎨 Customize Caption 🎨", "caption")],
        [("🪄 AutoClean", "autoclean"), ("🎉 Sticker", "sticker")],
        [("🔤 Word Control 🔤", "words")],
        [("✨ Prefix", "prefix"), ("✨ Suffix", "suffix")],
        [("⚙️ Manage Bot ⚙️", "manage")],
    ], "home"),
    "reactions": (T.REACTIONS, [], "help"),
    "buttons": (T.BUTTONS, [], "help"),
    "caption": (T.CAPTION, [
        [("📝 Set Caption", "setcap"), ("🗑 Del Caption", "delcap")],
        [("📘 Formats", "formats"), ("# Hashtag Mode", "hashtag")],
    ], "help"),
    "setcap": (T.SETCAP, [], "caption"),
    "delcap": (T.DELCAP, [], "caption"),
    "formats": (T.FORMATS, [], "caption"),
    "hashtag": (T.HASHTAG, [], "caption"),
    "autoclean": (T.AUTOCLEAN, [], "help"),
    "sticker": (T.STICKER, [], "help"),
    "words": (T.WORDS, [[("❌ Remove", "remove"), ("🔁 Replace", "replace")]], "help"),
    "remove": (T.REMOVE, [], "words"),
    "replace": (T.REPLACE, [], "words"),
    "prefix": (T.PREFIX, [], "help"),
    "suffix": (T.SUFFIX, [], "help"),
    "manage": (T.MANAGE, [
        [("📄 Details", "details"), ("♻️ Reset", "reset")],
        [("🔄 Copy Settings", "copy")],
    ], "help"),
    "details": (T.DETAILS, [], "manage"),
    "reset": (T.RESET, [], "manage"),
    "copy": (T.COPY, [], "manage"),
}


def _rows(rows):
    return [[B(label, callback_data=cb) for label, cb in row] for row in rows]


def _nav(back: str, close: bool = False):
    row = [B("↩️ Back", callback_data=back)]
    if close:
        row.append(B("❌ Close", callback_data="close"))
    return row


async def render(key: str, bot_username: str, mention: str = "") -> tuple[str, M]:
    if key == "home":
        rows = [[B("ℹ️ About", callback_data="about"), B("📚 Help", callback_data="help")],
                [B("⇆ Add Me To Your Channel ⇆",
                   url=f"https://t.me/{bot_username}?startchannel=true&admin=post_messages+edit_messages+delete_messages")]]
        if Config.WEBAPP_URL.startswith("https://"):
            rows.append([B("🌐 Open Web Panel", web_app=WebAppInfo(url=Config.WEBAPP_URL))])
        text = T.HOME.replace("{mention}", mention).replace("{maintainer}", Config.MAINTAINER)
        return text, M(rows)

    if key == "about":
        rows = []
        if Config.SOURCE_URL:
            rows.append([B("📂 Source Code", url=Config.SOURCE_URL)])
        row = []
        if Config.DONATE_URL:
            row.append(B("☕ Donate", url=Config.DONATE_URL))
        row.append(B("📊 Stats", callback_data="stats"))
        rows.append(row)
        rows.append(_nav("home"))
        return T.ABOUT.replace("{name}", Config.BOT_NAME), M(rows)

    if key == "stats":
        s = await db.stats()
        text = T.STATS.format(**s)
        rows = []
        if Config.WEBSITE_URL.startswith("http"):
            rows.append([B("🌐 Website", url=Config.WEBSITE_URL)])
        rows.append(_nav("about", close=True))
        return text, M(rows)

    text, rows, back = PAGES[key]
    markup = _rows(rows) + [_nav(back, close=(key == "help"))]
    return text, M(markup)
