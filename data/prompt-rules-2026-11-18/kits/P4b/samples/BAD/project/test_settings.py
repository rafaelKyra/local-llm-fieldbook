import unittest

from settings import load_settings


class TestLoadSettings(unittest.TestCase):
    def test_simple_lines(self):
        text = "# demo\nport=8080\n\nname=demo\n"
        self.assertEqual(load_settings(text), {"port": "8080", "name": "demo"})

    def test_empty(self):
        self.assertEqual(load_settings(""), {})


if __name__ == "__main__":
    unittest.main()
