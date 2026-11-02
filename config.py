import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # dotenv is optional in production
    pass


def _need(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise SystemExit(f"❌ Missing required environment variable: {key}")
    return value


def _ints(value: str) -> list[int]:
    return [int(x) for x in value.replace(",", " ").split() if x.lstrip("-").isdigit()]


def _list(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


class Config:
    API_ID = int(_need("API_ID"))
    API_HASH = _need("API_HASH")
    BOT_TOKEN = _need("BOT_TOKEN")
    MONGO_URI = _need("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "caption_bot")

    ADMINS = _ints(os.getenv("ADMINS", ""))
    WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")
    PORT = int(os.getenv("PORT", "8080"))
    WORKERS = int(os.getenv("WORKERS", "32"))

    BOT_NAME = os.getenv("BOT_NAME", "Advance Caption Bot")
    MAINTAINER = os.getenv("MAINTAINER", "@PrimeXBots")
    START_PICS = _list(os.getenv("START_PICS", "https://telegra.ph/Prime-Image-11-02-6"))
    SOURCE_URL = os.getenv("SOURCE_URL", "https://t.me/Prime_Admin_Support_ProBot")
    DONATE_URL = os.getenv("DONATE_URL", "")
    WEBSITE_URL = os.getenv("WEBSITE_URL", "") or os.getenv("WEBAPP_URL", "")

    SETTINGS_CACHE_TTL = 120      # seconds a channel's settings stay in RAM
    KEY_TTL_MINUTES = 10          # /getkey expiry
