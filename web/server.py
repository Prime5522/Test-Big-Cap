"""aiohttp server: serves the Telegram Mini App + a small JSON API.
Every /api request is authenticated with Telegram's signed `initData` (HMAC-SHA256)."""
import hashlib
import hmac
import html
import json
import re
import time
from pathlib import Path
from urllib.parse import parse_qsl

from aiohttp import web
from pyrogram.enums import ChatMemberStatus

from bot.core.buttons import parse_buttons
from bot.core.caption import build_caption
from bot.database import DEFAULTS, db
from config import Config

STATIC = Path(__file__).parent / "static"
SAMPLE = "Avengers.Endgame.2019.1080p.BluRay.x265.Hindi.English.ESub.mkv"
_verified: dict[tuple[int, int], float] = {}


# ── auth ─────────────────────────────────────────────────────────────────────
def verify_init_data(init_data: str, token: str, max_age: int = 86400) -> dict | None:
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        received = pairs.pop("hash")
        check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(hmac.new(secret, check.encode(), hashlib.sha256).hexdigest(), received):
            return None
        if time.time() - int(pairs.get("auth_date", 0)) > max_age:
            return None
        return json.loads(pairs["user"])
    except Exception:
        return None


@web.middleware
async def guard(request: web.Request, handler):
    if request.path.startswith("/api/"):
        user = verify_init_data(request.headers.get("X-Init-Data", ""), Config.BOT_TOKEN)
        if not user:
            return web.json_response({"error": "Open this panel from the bot inside Telegram."}, status=401)
        request["user"] = user
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:  # never leak a stack trace to the client
        return web.json_response({"error": "Server error"}, status=500)


async def manageable(request, chat_id: int):
    """Returns the channel doc if this user is (still) an admin of the channel."""
    uid, bot = request["user"]["id"], request.app["bot"]
    doc = await db.channel(chat_id)
    if not doc:
        return None
    if uid in Config.ADMINS:
        return doc
    if uid not in doc.get("admins", []):
        return None
    now, key = time.monotonic(), (uid, chat_id)
    if _verified.get(key, 0) > now:
        return doc
    try:
        mem = await bot.get_chat_member(chat_id, uid)
        ok = mem.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        ok = False
    if ok:
        _verified[key] = now + 300
        return doc
    await db.channels.update_one({"_id": chat_id}, {"$pull": {"admins": uid}})
    return None


# ── validation / sanitising ──────────────────────────────────────────────────
def clean(data: dict) -> dict:
    out = {}
    if "caption" in data:
        out["caption"] = (str(data["caption"] or "")[:3000]).strip() or None
    for k, n in (("prefix", 1000), ("suffix", 1000), ("buttons", 2000)):
        if k in data:
            out[k] = str(data[k] or "")[:n]
    for k in ("enabled", "react", "autoclean"):
        if k in data:
            out[k] = bool(data[k])
    if "remove" in data:
        out["remove"] = list(dict.fromkeys(str(w).strip()[:60] for w in (data["remove"] or []) if str(w).strip()))[:150]
    if "replace" in data:
        out["replace"] = [[str(a).strip()[:60], str(b).strip()[:60]] for a, b in
                          ((p + [""])[:2] for p in (data["replace"] or []) if isinstance(p, list) and p)
                          if str(a).strip()][:150]
    if "hashtags" in data:
        out["hashtags"] = [f for f in ("audio", "quality", "year") if f in (data["hashtags"] or [])]
    return out


_TAGS = re.compile(r"&lt;(/?)(b|i|u|s|code|pre|blockquote|spoiler)(?: expandable)?&gt;", re.I)
_A_OPEN = re.compile(r"&lt;a href=&quot;(https?://.+?)&quot;&gt;", re.I)


def sanitize(text: str) -> str:
    """Escape everything, then re-enable the small set of tags Telegram supports."""
    e = html.escape(text)
    e = _A_OPEN.sub(lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener noreferrer">', e)
    e = e.replace("&lt;/a&gt;", "</a>")

    def tag(m):
        close, name = m.group(1), m.group(2).lower()
        if name == "spoiler":
            return "</span>" if close else '<span class="spoiler">'
        return f"<{close}{name}>"
    return _TAGS.sub(tag, e)


def pack(doc: dict) -> dict:
    s = {**DEFAULTS, **(doc.get("settings") or {})}
    has_sticker = bool(s.pop("sticker", None))
    return {"id": doc["_id"], "title": doc.get("title", str(doc["_id"])), "files": doc.get("files", 0),
            "settings": s, "has_sticker": has_sticker}


# ── routes ───────────────────────────────────────────────────────────────────
async def index(request):
    return web.FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


async def health(request):
    return web.Response(text="ok")


async def bootstrap(request):
    user = request["user"]
    chans = await db.channels_for(user["id"])
    data = {
        "user": {"id": user["id"], "name": user.get("first_name", "")},
        "bot": request.app["bot"].me.username,
        "channels": [{"id": c["_id"], "title": c.get("title", str(c["_id"])), "files": c.get("files", 0)} for c in chans],
        "is_admin": user["id"] in Config.ADMINS,
    }
    if data["is_admin"]:
        data["stats"] = await db.stats()
    return web.json_response(data)


async def get_channel(request):
    doc = await manageable(request, int(request.match_info["id"]))
    if not doc:
        return web.json_response({"error": "Channel not found or no access."}, status=404)
    return web.json_response(pack(doc))


async def put_channel(request):
    chat_id = int(request.match_info["id"])
    if not await manageable(request, chat_id):
        return web.json_response({"error": "No access."}, status=403)
    body = await request.json()
    fields = clean(body.get("settings") or {})
    await db.update_settings(chat_id, **fields)
    return web.json_response({"ok": True})


async def reset_channel(request):
    chat_id = int(request.match_info["id"])
    if not await manageable(request, chat_id):
        return web.json_response({"error": "No access."}, status=403)
    await db.reset_settings(chat_id)
    return web.json_response({"ok": True})


async def copy_channel(request):
    src = int(request.match_info["id"])
    dst = int((await request.json()).get("to", 0))
    if src == dst or not await manageable(request, src) or not await manageable(request, dst):
        return web.json_response({"error": "You must be admin of both channels."}, status=403)
    await db.copy_settings(src, dst)
    return web.json_response({"ok": True})


async def preview(request):
    body = await request.json()
    s = {**DEFAULTS, **clean(body.get("settings") or {})}
    name = str(body.get("filename") or SAMPLE)[:300]
    text = build_caption(s, name, 2470000000, 6700, "Original caption sample", "Original caption sample")
    rows = [[{"text": t, "style": st} for t, _u, st in row] for row in parse_buttons(s["buttons"])]
    return web.json_response({"html": sanitize(text), "buttons": rows, "file": name})

async def connect_channel(request):
    user = request["user"]
    uid = user["id"]
    bot = request.app["bot"]
    body = await request.json()
    raw_target = str(body.get("channel", "")).strip()

    if not raw_target:
        return web.json_response({"error": "চ্যানেল ইউজারনেম বা আইডি দিন!"}, status=400)

    target = int(raw_target) if raw_target.lstrip("-").isdigit() else raw_target

    try:
        chat = await bot.get_chat(target)
    except Exception:
        return web.json_response({"error": "চ্যানেল পাওয়া যায়নি! বট অ্যাডমিন আছে তো?"}, status=404)

    try:
        bot_mem = await bot.get_chat_member(chat.id, "me")
        if bot_mem.status != ChatMemberStatus.ADMINISTRATOR:
            return web.json_response({"error": "বট ওই চ্যানেলে অ্যাডমিন নয়!"}, status=400)

        user_mem = await bot.get_chat_member(chat.id, uid)
        if user_mem.status not in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
            return web.json_response({"error": "আপনি ওই চ্যানেলের অ্যাডমিন নন!"}, status=403)
    except Exception:
        return web.json_response({"error": "পারমিশন চেক ব্যর্থ হয়েছে।"}, status=400)

    await db.add_channel(chat.id, chat.title or str(chat.id), owner_id=uid)
    await db.channels.update_one({"_id": chat.id}, {"$addToSet": {"admins": uid}})
    
    return web.json_response({"ok": True, "title": chat.title, "id": chat.id})


def create_app(bot) -> web.Application:
    app = web.Application(middlewares=[guard], client_max_size=256 * 1024)
    app["bot"] = bot
    app.add_routes([
        web.get("/", index), web.get("/health", health),
        web.get("/api/bootstrap", bootstrap),
        web.get(r"/api/channel/{id:-?\d+}", get_channel),
        web.put(r"/api/channel/{id:-?\d+}", put_channel),
        web.post("/api/channel/connect", connect_channel),
        web.post(r"/api/channel/{id:-?\d+}/reset", reset_channel),
        web.post(r"/api/channel/{id:-?\d+}/copy", copy_channel),
        web.post("/api/preview", preview),
    ])
    return app


async def start_web(bot) -> web.AppRunner:
    runner = web.AppRunner(create_app(bot), access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", Config.PORT).start()
    return runner
    
