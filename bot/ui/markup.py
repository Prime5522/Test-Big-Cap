import logging
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

log = logging.getLogger("markup")

# Kurigram এর ButtonStyle চেক করা
HAS_BUTTON_STYLE = False
try:
    from pyrogram.enums import ButtonStyle
    STYLE_MAP = {
        "primary": ButtonStyle.PRIMARY,  # 🔵 Dark Blue
        "success": ButtonStyle.SUCCESS,  # 🟢 Green
        "danger": ButtonStyle.DANGER,    # 🔴 Red
    }
    HAS_BUTTON_STYLE = True
except (ImportError, AttributeError):
    STYLE_MAP = {}

# যদি কোনো কারণে লাইব্রেরিতে কালার সাপোর্ট না করে, তখন ফলব্যাক ইমোজি
FALLBACK_EMOJI = {
    "primary": "🔵 ",
    "success": "🟢 ",
    "danger": "🔴 ",
    "warning": "🟡 ",
    "yellow": "🟡 ",
    "purple": "🟣 ",
    "orange": "🟠 ",
    "cyan": "🩵 ",
    "black": "⚫ ",
    "white": "⚪ ",
}


def _button(text: str, url: str, style: str | None = None) -> InlineKeyboardButton:
    text = text.strip()
    
    # ১. Kurigram থাকলে রিয়েল কালার বাটন তৈরি করবে
    if style and HAS_BUTTON_STYLE and style.lower() in STYLE_MAP:
        try:
            return InlineKeyboardButton(text, url=url, style=STYLE_MAP[style.lower()])
        except Exception:
            pass

    # ২. কালার সাপোর্ট না করলে ফলব্যাক (যদি ইমোজি না চান তবে খালি return InlineKeyboardButton(text, url=url) দিতে পারেন)
    prefix = FALLBACK_EMOJI.get(style.lower(), "") if style else ""
    return InlineKeyboardButton(prefix + text, url=url)


def to_markup(rows) -> InlineKeyboardMarkup | None:
    if not rows:
        return None
    return InlineKeyboardMarkup([[_button(*b) for b in row] for row in rows])
