"""Caption engine: turns a file name + settings into a final HTML caption."""
import html
import re

from .parser import (autoclean_name, autoclean_text, extract_title, hashtag, human_duration, human_size, parse,
                     remove_words, replace_words, split_ext)

DEFAULT_CAPTION = (
    "<b>{name}</b>\n\n"
    "📦 <b>Size:</b> {size}\n"
    "🎞 <b>Quality:</b> {quality}\n"
    "🔊 <b>Audio:</b> {audio}\n"
    "💬 <b>Subtitle:</b> {subtitle}\n"
    "⏱ <b>Duration:</b> {duration}"
)

VARIABLES = ("name", "title", "caption", "year", "size", "duration", "audio", "quality", "season",
             "episode", "subtitle", "ext")
_VAR_RE = re.compile(r"\{(" + "|".join(VARIABLES) + r")\}")
_TAG_RE = re.compile(r"<[^>]+>")
CAPTION_LIMIT = 1024


def build_vars(s: dict, filename: str, size=0, duration=0, cap_html: str = "", cap_plain: str = "") -> dict:
    stem, ext = split_ext(filename or "")
    stem = replace_words(remove_words(stem, s.get("remove", [])), s.get("replace", []))
    info = parse(stem)
    name = autoclean_name(stem) if s.get("autoclean") else stem

    if s.get("autoclean"):
        plain = replace_words(remove_words(cap_plain, s.get("remove", [])), s.get("replace", []))
        caption = html.escape(autoclean_text(plain))
    else:
        caption = replace_words(remove_words(cap_html, s.get("remove", [])), s.get("replace", []))

    tags = set(s.get("hashtags", []))
    audio = " ".join(map(hashtag, info["audio"])) if "audio" in tags else ", ".join(info["audio"])
    quality = " ".join(map(hashtag, info["quality"])) if "quality" in tags else " ".join(info["quality"])
    year = hashtag(info["year"]) if (info["year"] and "year" in tags) else info["year"]

    esc = html.escape
    return {
        "name": esc(name), "title": esc(extract_title(stem)), "caption": caption, "year": esc(year), "size": human_size(size),
        "duration": human_duration(duration), "audio": esc(audio), "quality": esc(quality),
        "season": info["season"], "episode": info["episode"], "subtitle": esc(info["subtitle"]),
        "ext": ext,
    }


def render(template: str, v: dict) -> str:
    """Substitute variables; any line whose variables are ALL empty is dropped."""
    out = []
    for line in template.split("\n"):
        keys = _VAR_RE.findall(line)
        if keys and not any(v.get(k) for k in keys):
            continue
        out.append(_VAR_RE.sub(lambda m: v.get(m.group(1), ""), line).rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def visible_len(text: str) -> int:
    return len(html.unescape(_TAG_RE.sub("", text)))


def build_caption(s: dict, filename: str, size=0, duration=0, cap_html: str = "", cap_plain: str = "") -> str:
    v = build_vars(s, filename, size, duration, cap_html, cap_plain)
    parts = []
    if s.get("prefix"):
        parts.append(render(s["prefix"], v))
    parts.append(render(s.get("caption") or DEFAULT_CAPTION, v))
    if s.get("suffix"):
        parts.append(render(s["suffix"], v))
    text = "\n".join(p for p in parts if p).strip()

    if not text:
        text = f"<b>{v['name']}</b>" if v["name"] else cap_html
    if visible_len(text) > CAPTION_LIMIT:               # never break HTML by cutting – fall back
        text = f"<b>{v['name'][:900]}</b>"
    return text
