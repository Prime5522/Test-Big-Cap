from pyrogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M, WebAppInfo
from bot.database import db
from config import Config
from . import texts as T

# PAGES ডিকশনারিতে "connect" যোগ করুন এবং Help মেনুতে বাটন দিন
PAGES: dict[str, tuple[str, list[list[tuple[str, str]]], str]] = {
    "help": (T.HELP, [
        [("🔗 Connect Channel", "connect_guide")],  # <-- হেল্প মেনুর শীর্ষে যুক্ত করা হলো
        [("🎭 Reactions", "reactions"), ("🔘 Buttons", "buttons")],
        [("🎨 Customize Caption 🎨", "caption")],
        [("🪄 AutoClean", "autoclean"), ("🎉 Sticker", "sticker")],
        [("🔤 Word Control 🔤", "words")],
        [("✨ Prefix", "prefix"), ("✨ Suffix", "suffix")],
        [("⚙️ Manage Bot ⚙️", "manage")],
    ], "home"),
    "connect_guide": (T.CONNECT_GUIDE, [], "help"), # <-- কানেক্ট গাইড পেজ
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
        # হোম স্ক্রিনেও সরাসরি "🔗 How to Connect" বাটন দেওয়া হলো
        rows = [
            [B("🔗 How to Connect", callback_data="connect_guide"), B("📚 Help", callback_data="help")],
            [B("➕ Add Me To Channel ➕",
               url=f"https://t.me/{bot_username}?startchannel=true&admin=post_messages+edit_messages+delete_messages")],
            [B("ℹ️ About", callback_data="about")]
        ]
        if Config.WEBAPP_URL.startswith("https://"):
            rows.insert(2, [B("🌐 Open Web Panel", web_app=WebAppInfo(url=Config.WEBAPP_URL))])
            
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
        if Config.WEBAPP_URL.startswith("https://"):
            rows.insert(2, [B("🌐 Open Web Panel", web_app=WebAppInfo(url=Config.WEBAPP_URL))])
        rows.append(_nav("about", close=True))
        return text, M(rows)

    text, rows, back = PAGES[key]
    markup = _rows(rows) + [_nav(back, close=(key == "help"))]
    return text, M(markup)
