"""Reader for the vendor's daily export."""
import datetime


def parse_date(text):
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError("bad date: %r" % text)


def parse_row(line):
    day, amount = line.split(",")
    return parse_date(day), float(amount)
