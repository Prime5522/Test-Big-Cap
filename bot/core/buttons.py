"""Parses the /btns syntax:  [Text](url[:primary|success|danger])  – one line = one row."""
import re

_BTN_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
STYLES = ("primary", "success", "danger", "warning", "yellow", "purple", "orange", "cyan", "black", "white")
_URL_OK = re.compile(r"^(https?://|tg://|t\.me/)", re.I)
MAX_ROWS, MAX_PER_ROW = 8, 4


def parse_buttons(raw: str) -> list[list[tuple[str, str, str | None]]]:
    rows = []
    for line in (raw or "").splitlines():
        row = []
        for text, target in _BTN_RE.findall(line):
            style = None
            for st in STYLES:
                if target.lower().endswith(":" + st):
                    target, style = target[: -len(st) - 1], st
                    break
            if not _URL_OK.match(target):
                continue
            if target.lower().startswith("t.me/"):
                target = "https://" + target
            row.append((text.strip()[:64], target, style))
            if len(row) >= MAX_PER_ROW:
                break
        if row:
            rows.append(row)
        if len(rows) >= MAX_ROWS:
            break
    return rows
