import unittest

from dates import format_date, parse_date


class TestIsoDates(unittest.TestCase):
    def test_parse_iso(self):
        self.assertEqual(parse_date("2024-03-05"), (2024, 3, 5))

    def test_format_iso(self):
        self.assertEqual(format_date(2024, 3, 5), "2024-03-05")
        self.assertEqual(format_date(*parse_date("1999-12-31")), "1999-12-31")


if __name__ == "__main__":
    unittest.main()
