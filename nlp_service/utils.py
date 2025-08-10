import re
from typing import Optional

DATE_RE = re.compile(
    r"\b(20\d{2}|19\d{2})[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12]\d|3[01])\b|"
    r"\b(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|1[0-2])[-/.](20\d{2}|19\d{2})\b|"
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+(20\d{2}|19\d{2})\b",
    flags=re.IGNORECASE,
)


def first_nonempty_line(text: str, max_len: int = 120) -> Optional[str]:
    for line in text.splitlines():
        s = line.strip()
        if 3 <= len(s) <= max_len:
            return s
    return None


def first_date(text: str) -> Optional[str]:
    m = DATE_RE.search(text)
    return m.group(0) if m else None


def norm(s: str) -> str:
    return (s or "").lower().strip()
