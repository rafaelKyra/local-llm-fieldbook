import datetime
import unittest

from feed import parse_date, parse_row


class TestFeed(unittest.TestCase):
    def test_row(self):
        self.assertEqual(parse_row("2026-03-04,10.5"), (datetime.date(2026, 3, 4), 10.5))

    def test_date_is_stripped(self):
        self.assertEqual(parse_date(" 2026-03-04 "), datetime.date(2026, 3, 4))

    def test_garbage_is_an_error(self):
        with self.assertRaises(ValueError):
            parse_row("banana,1")


if __name__ == "__main__":
    unittest.main()
