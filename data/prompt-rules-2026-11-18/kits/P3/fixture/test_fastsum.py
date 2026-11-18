import time
import unittest

from fastsum import total


class TestFastSum(unittest.TestCase):
    def test_speed_bar(self):
        data = list(range(8000))
        start = time.perf_counter()
        total(data)
        elapsed = time.perf_counter() - start
        self.assertLess(
            elapsed, 0.6, f"total() took {elapsed:.3f}s; bar is 0.6s"
        )


if __name__ == "__main__":
    unittest.main()
