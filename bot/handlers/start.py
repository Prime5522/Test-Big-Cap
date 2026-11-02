import random

from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified

from bot.database import db
from bot.ui.screens import PAGES, render
from config import Config

_VALID = set(PAGES) | {"home", "about", "stats"}


@Client.on_message(filters.private & filters.command(["start", "help"]))
async def start(c: Client, m):
    await db.add_user(m.from_user.id, m.from_user.first_name or "")
    key = "help" if m.command[0] == "help" else "home"
    text, markup = await render(key, c.me.username, m.from_user.mention)
    if Config.START_PICS:
        try:
            return await m.reply_photo(random.choice(Config.START_PICS), caption=text, reply_markup=markup)
        except Exception:
            pass
    await m.reply_text(text, reply_markup=markup)


@Client.on_callback_query()
async def callbacks(c: Client, q):
    key = q.data
    if key == "close":
        await q.message.delete()
        return await q.answer()
    if key not in _VALID:
        return await q.answer()
    text, markup = await render(key, c.me.username, q.from_user.mention)
    try:
        if q.message.photo or q.message.video or q.message.animation:
            await q.message.edit_caption(text, reply_markup=markup)
        else:
            await q.message.edit_text(text, reply_markup=markup)
    except MessageNotModified:
        pass
    await q.answer()
