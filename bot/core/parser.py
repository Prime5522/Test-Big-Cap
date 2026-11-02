"""Pure-python filename parsing & text cleaning helpers (no Telegram imports)."""
import re
from datetime import datetime

KNOWN_EXT = {
    "mkv", "mp4", "avi", "mov", "webm", "wmv", "flv", "m4v", "ts", "mpg", "mpeg", "3gp",
    "mp3", "flac", "m4a", "aac", "wav", "ogg", "opus", "zip", "rar", "7z", "pdf", "epub",
    "srt", "ass", "vtt", "apk", "iso", "cbz", "cbr", "txt",
}
_EXT_RE = re.compile(r"\.([A-Za-z0-9]{2,5})$")

_B = r"(?<![A-Za-z0-9])"   # left word boundary that treats . _ - as separators
_E = r"(?![A-Za-z0-9])"

_RES_RE = re.compile(_B + r"(2160p|1440p|1080p|720p|576p|480p|360p|4k|8k)" + _E, re.I)
_SRC_RE = re.compile(
    _B + r"(WEB[-._ ]?DL|WEB[-._ ]?Rip|Blu[-._ ]?Ray|BRRip|BDRip|HDRip|HDTV|DVDRip|HD[-._ ]?CAM|"
    r"CAM[-._ ]?Rip|PreDVD|HEVC|x265|x264|10[-._ ]?bit|HDR10|HDR)" + _E, re.I)
_CANON_Q = {
    "webdl": "WEB-DL", "webrip": "WEBRip", "bluray": "BluRay", "brrip": "BRRip", "bdrip": "BDRip",
    "hdrip": "HDRip", "hdtv": "HDTV", "dvdrip": "DVDRip", "hdcam": "HDCAM", "camrip": "CAMRip",
    "predvd": "PreDVD", "hevc": "HEVC", "x265": "x265", "x264": "x264", "10bit": "10bit",
    "hdr": "HDR", "hdr10": "HDR10", "4k": "4K", "8k": "8K",
}

_LANG_MAP = {
    "hin": "Hindi", "eng": "English", "dualaudio": "Dual Audio", "multiaudio": "Multi Audio",
}
_AUD_RE = re.compile(
    _B + r"(dual[-._ ]?audio|multi[-._ ]?audio|hindi|english|tamil|telugu|malayalam|kannada|bengali|"
    r"punjabi|marathi|gujarati|urdu|japanese|korean|chinese|spanish|french|german|russian|arabic|"
    r"turkish|thai|indonesian|hin|eng)" + _E, re.I)

_SUB_RE = re.compile(
    _B + r"(E[-._ ]?Subs?|M[-._ ]?Subs?|Multi[-._ ]?Subs?|(?:Eng(?:lish)?|Hindi|Hin)[-._ ]?Subs?|Subs?)" + _E, re.I)

_SE_RE = re.compile(_B + r"S(\d{1,2})[-._ ]?E(?:P)?(\d{1,4})" + _E, re.I)
_S_RE = re.compile(_B + r"(?:Season[-._ ]?|S)(\d{1,2})" + _E, re.I)
_EP_RE = re.compile(_B + r"(?:Episode[-._ ]?|EP|E)(\d{1,4})" + _E, re.I)
_YEAR_RE = re.compile(_B + r"((?:19|20)\d{2})" + _E)

_URL_RE = re.compile(r"(https?://\S+|www\.\S+|\bt\.me/\S+)", re.I)
_MENTION_RE = re.compile(r"(?<!\w)@\w+")
_SYMBOL_RE = re.compile(r"[^\w\s\-'&+()]", re.UNICODE)


def split_ext(filename: str) -> tuple[str, str]:
    m = _EXT_RE.search(filename or "")
    if m and m.group(1).lower() in KNOWN_EXT:
        return filename[: m.start()], m.group(1).lower()
    return filename or "", ""


def _dedup(items):
    seen, out = set(), []
    for i in items:
        k = i.lower()
        if k not in seen:
            seen.add(k)
            out.append(i)
    return out


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def parse(stem: str) -> dict:
    """Extract year/quality/audio/subtitle/season/episode from a file name stem."""
    info = {"year": "", "quality": [], "audio": [], "subtitle": "", "season": "", "episode": ""}

    # subtitle first, then blank it so "English Sub" doesn't become an audio language
    work = stem
    sm = _SUB_RE.search(work)
    if sm:
        k = _norm(sm.group(1))
        if k.startswith("m"):
            info["subtitle"] = "MSub"
        elif k in ("esub", "esubs"):
            info["subtitle"] = "ESub"
        elif k in ("sub", "subs"):
            info["subtitle"] = "Sub"
        else:
            lang = "English" if k.startswith("eng") else "Hindi"
            info["subtitle"] = f"{lang} Sub"
        work = work[: sm.start()] + " " + work[sm.end():]

    res = [("4K" if m.lower() == "4k" else "8K" if m.lower() == "8k" else m.lower()) for m in _RES_RE.findall(work)]
    src = [_CANON_Q.get(_norm(m), m) for m in _SRC_RE.findall(work)]
    info["quality"] = _dedup(res[:1] + src)

    aud = []
    for m in _AUD_RE.findall(work):
        k = _norm(m)
        aud.append(_LANG_MAP.get(k, m.title()))
    info["audio"] = _dedup(aud)

    se = _SE_RE.search(work)
    if se:
        info["season"], info["episode"] = se.group(1).zfill(2), se.group(2).zfill(2)
    else:
        s, e = _S_RE.search(work), _EP_RE.search(work)
        info["season"] = s.group(1).zfill(2) if s else ""
        info["episode"] = e.group(1).zfill(2) if e else ""

    years = [y for y in _YEAR_RE.findall(work) if int(y) <= datetime.now().year + 1]
    info["year"] = years[-1] if years else ""
    return info


def human_size(n) -> str:
    if not n:
        return ""
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
        n /= 1024


def human_duration(sec) -> str:
    sec = int(sec or 0)
    if sec <= 0:
        return ""
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s" if m else f"{s}s"


def autoclean_name(name: str) -> str:
    name = _URL_RE.sub(" ", name)
    name = _MENTION_RE.sub(" ", name)
    name = re.sub(r"(?<!\d)\.|\.(?!\d)|_", " ", name)   # keep 5.1 / 2.0
    name = _SYMBOL_RE.sub(" ", name)
    return re.sub(r"\s{2,}", " ", name).strip(" -")


def autoclean_text(text: str) -> str:
    text = _URL_RE.sub("", text)
    text = _MENTION_RE.sub("", text)
    text = _SYMBOL_RE.sub(lambda m: m.group(0) if m.group(0) in "\n" else "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return "\n".join(l.strip() for l in text.split("\n")).strip()


def _word_regex(words):
    words = sorted({w for w in words if w}, key=len, reverse=True)
    if not words:
        return None
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(w) for w in words) + r")(?!\w)", re.I)


def remove_words(text: str, words: list[str]) -> str:
    rx = _word_regex(words)
    if not rx or not text:
        return text
    return re.sub(r"[ \t]{2,}", " ", rx.sub("", text)).strip()


def replace_words(text: str, pairs: list) -> str:
    """pairs: [[old, new], ...] – case-insensitive, longer matches win."""
    if not pairs or not text:
        return text
    table = {str(o).lower(): str(n) for o, n in pairs if o}
    rx = _word_regex(table.keys())
    return rx.sub(lambda m: table.get(m.group(0).lower(), m.group(0)), text) if rx else text


def hashtag(value: str) -> str:
    return "#" + re.sub(r"[^A-Za-z0-9]", "", value)


def extract_title(stem: str) -> str:
    """Clean title only – text before the first year / resolution / season marker."""
    cut = len(stem)
    for rx in (_YEAR_RE, _RES_RE, _SE_RE, _S_RE, _SRC_RE):
        m = rx.search(stem)
        if m and m.start() > 2:
            cut = min(cut, m.start())
    return autoclean_name(stem[:cut])
