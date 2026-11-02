import html

from bot.core.caption import VARIABLES


def _q(title: str) -> str:
    return f"<blockquote><b>{title}</b></blockquote>\n"


HOME = (
    "👋 <b>Hello {mention},</b>\n\n"
    "I am a smart advanced caption bot built for professional channel management.\n\n"
    "I auto-generate captions, clean file names, add buttons, hashtags and much more — automatically.\n\n"
    "<blockquote> 🌿 ᴍᴀɪɴᴛᴀɪɴᴇᴅ ʙʏ  <a href='https://t.me/PrimeXBots'>ᴘʀɪᴍᴇXʙᴏᴛꜱ</a></blockquote>"
)

HELP = (
    _q("❓ Need Help?")
    + "\nYou can configure every feature using the buttons below.\n\n"
    "📌 <b>Note:</b> <i>All commands work only inside your channel.</i>\n"
    "🌐 Prefer a visual editor? Open the <b>Web Panel</b> from the main menu."
)

REACTIONS = (
    _q("🎭 Reaction Commands")
    + "\n<i>Auto-add a random emoji reaction to every channel post.</i>\n\n"
    "➤ <code>/react</code> — Enable reactions\n➤ <code>/reactoff</code> — Disable reactions"
)

BUTTONS = (
    _q("🔘 Button Commands")
    + "\n<i>Add inline link buttons under every post — download, support, website…</i>\n\n"
    "➤ <code>/btns</code> — Set custom buttons\n➤ <code>/btnsoff</code> — Remove all buttons\n\n"
    "🔹 <b>Examples</b>\n"
    "▸ Normal:\n<code>/btns [PrimeXBots](https://t.me/PrimeXBots)</code>\n\n"
    "▸ With style:\n<code>/btns [PrimeXBots](https://t.me/PrimeXBots:primary)</code>\n\n"
    "ℹ️ <b>Available Button Styles & Colors:</b>\n"
    "🔹 <code>:primary</code> — 🔵 Blue\n"
    "🔹 <code>:success</code> — 🟢 Green\n"
    "🔹 <code>:danger</code> — 🔴 Red\n"
    "🔹 <code>:warning</code> — 🟡 Yellow\n"
    "🔹 <code>:purple</code> — 🟣 Purple\n"
    "🔹 <code>:orange</code> — 🟠 Orange\n"
    "🔹 <code>:cyan</code> — 🩵 Cyan\n"
    "🔹 <code>:black</code> — ⚫ Black\n"
    "🔹 <code>:white</code> — ⚪ White\n\n"
    "🔶 <i>Omit the suffix for a normal button without any style.</i>\n\n"
    "🔹 <b>Layout</b>\n"
    "▸ Same line = same row:\n"
    "<code>/btns [PrimeXBots](https://t.me/PrimeXBots:primary) [Updates](https://t.me/PrimeXBots:success)</code>\n\n"
    "▸ New line = new row:\n"
    "<code>/btns [PrimeXBots](https://t.me/PrimeXBots:primary)\n[Updates](https://t.me/PrimeXBots:purple)</code>"
)

CAPTION = (
    _q("📝 Customize Caption")
    + "\n<i>Generate captions from file names using variable-based templates.</i>\n\n"
    "Use the buttons below to:\n• Set or delete your custom caption\n• View all supported variable formats\n"
    "• Turn audio / quality / year into hashtags"
)

_VAR_DOC = {
    "name": "File name", "title": "Clean title only", "caption": "Original caption", "year": "Release year",
    "size": "File size", "duration": "Media length", "audio": "Audio language", "quality": "Video quality",
    "season": "Season number", "episode": "Episode number", "subtitle": "Subtitle language", "ext": "File extension",
}
SETCAP = (
    _q("✏️ Custom Caption")
    + "\n➤ <code>/setcap [text]</code> — Set a fully custom caption using dynamic variables.\n\n"
    "<b>Available variables:</b>\n"
    + "\n".join(f"➤ <code>{{{k}}}</code> — {_VAR_DOC[k]}" for k in VARIABLES)
    + "\n\n<b>Example:</b>\n<code>/setcap &lt;b&gt;{title}&lt;/b&gt; ({year})\n🔊 {audio} • 📺 {quality}\n💾 {size}</code>\n\n"
    "💡 Lines whose variables are all empty are removed automatically.\n"
    "⚠️ Variables are auto-detected from the file name."
)
DELCAP = (
    _q("🗑 Delete Caption")
    + "\n➤ <code>/delcap</code> — Remove the custom caption and return to the default.\n\n"
    "⚠️ Will remove all custom variables/formats."
)

_FORMATS = [
    ("Bold", "<b>{name}</b>"), ("Italic", "<i>{name}</i>"), ("Underline", "<u>{name}</u>"),
    ("Strike", "<s>{name}</s>"), ("Spoiler", "<spoiler>{name}</spoiler>"), ("Mono", "<code>{name}</code>"),
    ("Multiline pre block", "<pre>{name}</pre>"), ("Block quote", "<blockquote>{name}</blockquote>"),
    ("Expandable quote", "<blockquote expandable>{name}</blockquote>"),
    ("Hyperlink", '<a href="https://t.me/example">{name}</a>'),
]
FORMATS = _q("🔰 Available Caption Formats") + "\n" + "\n\n".join(
    f"➤ <b>{t}</b>\n☞ <code>{html.escape(c)}</code>" for t, c in _FORMATS)

HASHTAG = (
    _q("# Hashtag Mode")
    + "\n<i>Convert audio, quality and year into hashtags automatically.</i>\n\n"
    "➤ <code>/hashtag audio|quality|year</code> — Enable for selected fields\n"
    "➤ <code>/showhashtag</code> — View enabled fields\n➤ <code>/clearhashtag</code> — Disable all hashtags\n\n"
    "<b>Example:</b> <code>/hashtag audio|year</code>\n\n"
    "🔹 {audio} → #Hindi #English\n🔹 {year} → #2023\n🔹 {quality} → #1080p #WEBDL"
)

AUTOCLEAN = (
    _q("🪄 Auto Clean")
    + "\n➤ <code>/autoclean</code> — Enable auto clean mode\n➤ <code>/autocleanoff</code> — Disable auto clean\n\n"
    "🔹 Removes symbols, links, mentions &amp; emojis\n🔹 Fixes extra spaces &amp; blank lines\n"
    "🔹 Corrects the file extension (e.g. .mkv, .mp4)\n🔹 Makes captions clean, formatted &amp; professional"
)

STICKER = (
    _q("🎉 Sticker Commands")
    + "\n<i>Send a custom sticker after every post.</i>\n\n"
    "➤ <code>/setsticker</code> (reply to a sticker) — Set sticker\n➤ <code>/clearsticker</code> — Remove sticker"
)

WORDS = (
    _q("🔤 Word Control")
    + "\n<i>Use the options below to filter words from file names or captions.</i>\n\n"
    "This helps you remove or replace words as you need."
)

REMOVE = (
    _q("❌ Remove Words")
    + "\n➤ <code>/remwords word1|word2|word3</code> — Set remove rules\n"
    "➤ <code>/remwords + word4|word5</code> — Append new words\n➤ <code>/remwordsoff</code> — Clear all rules\n\n"
    "🔹 Removes specific words from file names &amp; captions\n🔹 Matching is case-insensitive"
)

REPLACE = (
    _q("🔁 Replace Commands")
    + "\n<i>Auto-replace words/names in file names &amp; captions.</i>\n\n"
    "➤ <code>/replace old:new|old2:new2</code> — Set replace rules\n"
    "➤ <code>/replace + old:new</code> — Append new rules\n➤ <code>/replaceoff</code> — Clear all rules\n\n"
    "🔹 Format: <code>old:new</code>\n🔹 Matching is case-insensitive\n🔹 Longer matches are prioritized"
)

PREFIX = (
    _q("🔤 Prefix Commands")
    + "\n<i>Add custom text before the auto caption — brands, tags, etc.</i>\n\n"
    "➤ <code>/prefix [text]</code> — Set a prefix\n➤ <code>/prefixoff</code> — Remove prefix"
)

SUFFIX = (
    _q("🔚 Suffix Commands")
    + "\n<i>Add custom text after the caption — signature, source, etc.</i>\n\n"
    "➤ <code>/suffix [text]</code> — Set a suffix\n➤ <code>/suffixoff</code> — Remove suffix"
)

MANAGE = (
    _q("⚙️ Manage Bot")
    + "\n<i>Access useful channel tools:</i>\n\n• View all enabled bot features for this channel\n"
    "• Pause the bot or preview your caption\n• Reset channel settings back to default\n\n"
    "Use only if you want full config control."
)

DETAILS = (
    _q("📄 Details")
    + "\n➤ <code>/details</code> — Show current channel config\n\n"
    "🔹 Displays active settings: Caption, Prefix, Suffix, Reactions, Sticker, Buttons, Word filters, etc.\n"
    "➤ <code>/preview</code> — Post a sample caption using your current settings\n"
    "➤ <code>/pause</code> · <code>/resume</code> — Temporarily stop / restart the bot in this channel"
)

RESET = (
    _q("♻️ Reset")
    + "\n➤ <code>/reset</code> — Reset all channel settings\n\n"
    "🔹 Removes all custom captions, set buttons, reactions, stickers, and word filters.\n\n"
    "⚠️ Use with caution. This action can't be undone."
)

COPY = (
    _q("🔄 Copy Settings")
    + "\n<i>Easily duplicate all channel settings to another channel using a secure key.</i>\n\n"
    "⚙️ <b>How it works</b>\n➤ <code>/getkey</code> — Generate a temporary settings key (in the source channel)\n"
    "➤ <code>/apply KEY</code> — Apply the settings (in the target channel)\n\n"
    "🔐 <b>The key is:</b>\n• One-time usable\n• Auto-expires in 10 minutes\n• Auto-deleted from the chat after 30 s\n\n"
    "⚠️ Make sure the bot is admin in both channels.\n🌐 The Web Panel can copy settings without any key."
)

ABOUT = (
    _q("🤖 Bot Information")
    + "\n▸ <b>Name:</b> {name}\n▸ <b>Version:</b> v4.0\n▸ <b>Library:</b> Pyrofork (MTProto)\n"
    "▸ <b>Database:</b> MongoDB\n▸ <b>Language:</b> Python 3\n▸ <b>Control:</b> Commands + Web Panel\n\n"
    "🌟 <i>Thanks for using the bot!</i>"
)

STATS = (
    _q("📊 Bot Statistics")
    + "\n👤 <b>Total Users:</b> {users}\n📢 <b>Total Channels:</b> {channels}\n"
    "✅ <b>Files Processed:</b> {files}\n\n<i>Everything is running smoothly ✨</i>"
)

PRIVATE_HINT = (
    "ℹ️ This command works <b>inside your channel</b>.\n\n"
    "Add me as admin (post + edit + delete messages), then send the command there.\n"
    "Or use the <b>Web Panel</b> from /start for a visual editor."
)
