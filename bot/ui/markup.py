from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

_EMOJI = {"primary": "🔵 ", "success": "🟢 ", "danger": "🔴 "}


def _button(text: str, url: str, style: str | None) -> InlineKeyboardButton:
    if style:
        try:                                   # native coloured buttons (newer Telegram/Pyrogram builds)
            return InlineKeyboardButton(text, url=url, style=style)
        except Exception:
            return InlineKeyboardButton(_EMOJI[style] + text, url=url)   # graceful fallback
    return InlineKeyboardButton(text, url=url)


def to_markup(rows) -> InlineKeyboardMarkup | None:
    if not rows:
        return None
    return InlineKeyboardMarkup([[_button(*b) for b in row] for row in rows])
