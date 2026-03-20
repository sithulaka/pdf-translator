import unittest
import os
from pdf_translator.cache import load_cache, save_cache, get_cache_key, CachedTranslator


class TestCacheKey(unittest.TestCase):
    def test_same_input_same_key(self):
        self.assertEqual(get_cache_key("hello", "si"), get_cache_key("hello", "si"))

    def test_different_text_different_key(self):
        self.assertNotEqual(get_cache_key("hello", "si"), get_cache_key("world", "si"))

    def test_different_lang_different_key(self):
        self.assertNotEqual(get_cache_key("hello", "si"), get_cache_key("hello", "ta"))


class TestCacheIO(unittest.TestCase):
    def setUp(self):
        self.cache_path = os.path.join(os.path.dirname(__file__), 'test_cache.json')

    def tearDown(self):
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)

    def test_save_and_load(self):
        data = {"key1": "value1"}
        save_cache(data, self.cache_path)
        self.assertEqual(load_cache(self.cache_path), data)

    def test_load_missing_file(self):
        self.assertEqual(load_cache('/nonexistent/path.json'), {})


class TestCachedTranslator(unittest.TestCase):
    def setUp(self):
        self.cache_path = os.path.join(os.path.dirname(__file__), 'test_ct.json')
        self.call_count = 0
        def fake_translate(text, **kwargs):
            self.call_count += 1
            return f"translated:{text}"
        self.ct = CachedTranslator(fake_translate, cache_path=self.cache_path)

    def tearDown(self):
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)

    def test_first_call_translates(self):
        result = self.ct.translate("hello", target_lang='si')
        self.assertEqual(result, "translated:hello")
        self.assertEqual(self.call_count, 1)

    def test_second_call_uses_cache(self):
        self.ct.translate("hello", target_lang='si')
        self.ct.translate("hello", target_lang='si')
        self.assertEqual(self.call_count, 1)

    def test_different_text_translates_again(self):
        self.ct.translate("hello", target_lang='si')
        self.ct.translate("world", target_lang='si')
        self.assertEqual(self.call_count, 2)


if __name__ == "__main__":
    unittest.main()
