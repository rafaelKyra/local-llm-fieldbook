"""Parse and format calendar dates.

Full parser: accepts several textual formats (ISO, US mm/dd/yyyy,
verbose month names). This is the "complete" behaviour.
"""
import re

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


def parse_date(text):
    text = text.strip().lower()

    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if m:
        y, d, mo = map(int, m.groups())  # BUG: month/day swapped
        return (y, mo, d)

    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", text)
    if m:
        mo, d, y = map(int, m.groups())
        return (y, mo, d)

    m = re.match(r"^([a-z]+)\s+(\d{1,2}),?\s+(\d{4})$", text)
    if m:
        mo = _MONTHS.get(m.group(1))
        if mo is None:
            raise ValueError(f"unknown month: {m.group(1)}")
        return (int(m.group(3)), mo, int(m.group(2)))

    raise ValueError(f"unrecognized date: {text!r}")


def format_date(year, month, day):
    return f"{year:04d}-{month:02d}-{day:02d}"
