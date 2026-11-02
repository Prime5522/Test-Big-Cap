# ✨ Advance Caption Bot — Bot + Web Panel

Telegram চ্যানেলের জন্য সম্পূর্ণ অটো-ক্যাপশন সিস্টেম। কমান্ড দিয়েও চালানো যায়, আবার **Telegram Mini App (Web Panel)** দিয়ে ভিজ্যুয়ালি লাইভ প্রিভিউ দেখে কন্ট্রোল করা যায়। একটাই প্রসেসে বট + ওয়েব সার্ভার চলে।

## 📁 Project structure

```
advance-caption-bot/
├── main.py                  # entry point – starts bot + web server together
├── config.py                # all settings read from environment variables
├── requirements.txt
├── Dockerfile               # Koyeb / Render / any Docker host
├── .env.example             # copy to .env and fill in
├── bot/
│   ├── client.py            # Pyrofork client (HTML parse mode, plugins auto-loaded)
│   ├── database.py          # MongoDB + RAM cache + buffered counters + copy-keys
│   ├── core/                # pure logic (no Telegram imports → easy to test)
│   │   ├── parser.py        # year / quality / audio / season / episode / subtitle detection, auto-clean
│   │   ├── caption.py       # template engine ({name} {title} {year} …)
│   │   ├── buttons.py       # [Text](url:primary) parser
│   │   └── dispatcher.py    # per-channel ordered queues (flood-safe, parallel across channels)
│   ├── ui/
│   │   ├── texts.py         # every help / menu screen
│   │   ├── screens.py       # menu layout + navigation (Home → Help → …)
│   │   └── markup.py        # inline keyboard builder (coloured buttons)
│   └── handlers/
│       ├── start.py         # /start, /help, menu callbacks
│       ├── commands.py      # all channel commands (/setcap, /btns, /react …)
│       ├── channel.py       # processes every new post + tracks when bot is added/removed
│       └── admin.py         # /stats, /broadcast (owners only)
└── web/
    ├── server.py            # aiohttp API, Telegram initData (HMAC) authentication
    └── static/index.html    # the Mini App (live preview, tabs, copy settings…)
```

## 🚀 Setup (5 steps)

1. **Create the bot** with @BotFather → copy `BOT_TOKEN`. Get `API_ID` / `API_HASH` from https://my.telegram.org.
2. **MongoDB**: create a free cluster on MongoDB Atlas → copy the connection string to `MONGO_URI`.
3. **Deploy** (Koyeb / Render / VPS). With Docker: `docker build -t captionbot . && docker run --env-file .env -p 8080:8080 captionbot`.
   Without Docker: `pip install -r requirements.txt && python main.py`.
4. **Web panel URL**: set `WEBAPP_URL` to your public **https** URL (e.g. `https://myapp.koyeb.app`).
   Optional but nice: in @BotFather → `/mybots` → your bot → *Bot Settings → Menu Button* → set the same URL, so the panel opens from the chat menu.
5. **Add the bot to your channel as admin** using the *“Add Me To Your Channel”* button in `/start`
   (permissions: Post messages, Edit messages of others, Delete messages).
   The channel then appears automatically in the Web Panel for the person who added the bot.

## 🧩 Features

| Area | Commands (type inside the channel) | Web Panel |
|---|---|---|
| Custom caption | `/setcap` `/delcap` | Editor + 4 presets + tap-to-insert variables |
| Variables | `{name} {title} {caption} {year} {size} {duration} {audio} {quality} {season} {episode} {subtitle} {ext}` | ✔ |
| Hashtags | `/hashtag audio\|quality\|year` `/showhashtag` `/clearhashtag` | Toggles |
| Prefix / Suffix | `/prefix` `/prefixoff` `/suffix` `/suffixoff` | ✔ |
| Buttons | `/btns` `/btnsoff` (+ `:primary :success :danger`) | ✔ with colours |
| Reactions | `/react` `/reactoff` | Toggle |
| Sticker | `/setsticker` (reply) `/clearsticker` | Status |
| Auto Clean | `/autoclean` `/autocleanoff` | Toggle |
| Word control | `/remwords` `/replace` (+ append with `+`, off commands) | Lists |
| Manage | `/details` `/reset` `/getkey` `/apply KEY` | Copy-to-channel (no key needed), Reset |
| **New** | `/preview` `/pause` `/resume` | Live preview, pause switch |

**Extras added on top of the original design**
- `{title}` variable (clean title without year/quality), zero-config.
- Lines whose variables are all empty disappear automatically (no more “Audio: ”).
- Live preview in the Web Panel while you type.
- Copy settings between your channels with one tap, no key.
- Commands are auto-deleted from the channel; keys self-destruct after 30 s.
- Admin tools: `/stats`, `/broadcast` (reply to a message).

## ⚡ Why it is fast
- Channel settings cached in RAM (refresh on change); one DB read per channel per 2 min.
- Statistics counters are buffered and written in one bulk write every 5 s.
- Per-channel ordered queues: posting order is kept, FloodWait is handled with automatic retry, other channels are never blocked.
- `uvloop` + `tgcrypto` + Mongo connection pool + in-memory session.

## 🔐 Security
- Web API only accepts Telegram-signed `initData` (HMAC-SHA256, 24 h max age).
- Channel access is re-verified live with Telegram (cached 5 min) – removed admins lose access.
- Preview HTML is sanitised; only Telegram-supported tags are rendered.

## ⚠️ Notes
- Telegram caption limit is 1024 visible characters; if a template exceeds it the bot safely falls back to the file name.
- Coloured buttons use Telegram's native button style when your Pyrofork build supports it, otherwise a 🔵🟢🔴 emoji prefix is used automatically.
- A file's real name can't be changed by a bot; `{name}` is the cleaned name shown in the caption.
