import unittest
from pdf_translator.engines import translate_text, create_engine


class TestTranslateText(unittest.TestCase):
    def test_empty_text(self):
        self.assertEqual(translate_text(""), "")

    def test_none_text(self):
        self.assertEqual(translate_text(None), "")

    def test_whitespace(self):
        self.assertEqual(translate_text("   "), "")

    def test_short_text(self):
        result = translate_text("Hello")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_long_text(self):
        long_text = "This is a test sentence. " * 300
        result = translate_text(long_text)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_google_engine(self):
        result = translate_text("Hello", engine_name='google')
        self.assertIsInstance(result, str)

    def test_unknown_engine_raises(self):
        with self.assertRaises(ValueError):
            create_engine('nonexistent', 'si')


if __name__ == "__main__":
    unittest.main()
