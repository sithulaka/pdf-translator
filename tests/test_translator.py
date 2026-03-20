import unittest
from pdf_translator.translator import translate_text

class TestTranslateText(unittest.TestCase):
    def test_empty_text_returns_empty_string(self):
        result = translate_text("")
        self.assertEqual(result, "")

    def test_none_text_returns_empty_string(self):
        result = translate_text(None)
        self.assertEqual(result, "")

    def test_whitespace_only_returns_empty_string(self):
        result = translate_text("   ")
        self.assertEqual(result, "")

    def test_short_text_translates(self):
        result = translate_text("Hello")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_long_text_does_not_crash(self):
        long_text = "This is a test sentence. " * 300
        result = translate_text(long_text)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

if __name__ == "__main__":
    unittest.main()
