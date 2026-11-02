from pyrogram import Client, enums

from config import Config


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="caption_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=Config.WORKERS,
            parse_mode=enums.ParseMode.HTML,
            plugins={"root": "bot.handlers"},
            sleep_threshold=30,
            max_concurrent_transmissions=4,
            in_memory=True,
        )
