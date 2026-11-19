"""Reader for the vendor's daily export."""
import datetime


def parse_date(text):
    return datetime.datetime.strptime(text.strip(), "%Y-%m-%d").date()


def parse_row(line):
    day, amount = line.split(",")
    return parse_date(day), float(amount)
