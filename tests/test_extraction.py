import unittest
from main import extract_keywords

class TestExtraction(unittest.TestCase):
    def test_extract_keywords_basic(self):
        text = "トヨタが新車を発表 ソニーも新製品を発売"
        words = extract_keywords(text)
        self.assertIn("トヨタ", words)
        self.assertIn("ソニー", words)
        self.assertIn("新車", words)

if __name__ == '__main__':
    unittest.main()
