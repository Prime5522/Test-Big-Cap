import asyncio
import logging

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

from pyrogram import idle

from bot.client import Bot
from bot.database import db
from web.server import start_web

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("pyrogram").setLevel(logging.WARNING)
log = logging.getLogger("main")


async def main():
    await db.init()
    bot = Bot()
    await bot.start()
    runner = await start_web(bot)
    log.info("✅ @%s is running – web panel on the same process", bot.me.username)
    await idle()
    await runner.cleanup()
    await bot.stop()
    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
