"""Parse and format ISO dates."""
import re

_DATE_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")


def parse_date(text):
    m = _DATE_RE.match(text.strip())
    if not m:
        raise ValueError(f"expected ISO date YYYY-MM-DD, got {text!r}")
    return tuple(map(int, m.groups()))


def format_date(year, month, day):
    return f"{year:04d}-{month:02d}-{day:02d}"
