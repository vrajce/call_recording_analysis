import unittest
from chat_backend import preview_result


class TestPreview(unittest.TestCase):
    def test_preview_table(self):
        cols = ["a", "b"]
        rows = [(1, "x"), (2, "yy")]
        out = preview_result(cols, rows, limit=2)
        self.assertIn("a | b", out)
        self.assertIn("1 | x", out)
        self.assertIn("2 | yy", out)


if __name__ == "__main__":
    unittest.main()

