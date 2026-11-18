import os
import tempfile
import unittest

from report import save_report


class TestSaveReport(unittest.TestCase):
    def test_writes_text(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "report.txt")
            save_report(p, "hello")
            with open(p, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "hello")

    def test_replaces_old_text(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "report.txt")
            save_report(p, "old")
            save_report(p, "new")
            with open(p, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "new")


if __name__ == "__main__":
    unittest.main()
