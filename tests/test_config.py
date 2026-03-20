import unittest
import os
import tempfile
from pdf_translator.config import load_config, DEFAULTS


class TestConfig(unittest.TestCase):
    def test_defaults_returned_without_file(self):
        config = load_config(None)
        self.assertEqual(config['target_language'], 'si')
        self.assertEqual(config['engine'], 'google')

    def test_missing_file_returns_defaults(self):
        config = load_config('/nonexistent/config.yaml')
        self.assertEqual(config, DEFAULTS)

    def test_file_overrides_defaults(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("target_language: ta\nengine: mymemory\n")
            path = f.name
        try:
            config = load_config(path)
            self.assertEqual(config['target_language'], 'ta')
            self.assertEqual(config['engine'], 'mymemory')
            self.assertEqual(config['output_format'], 'txt')
        finally:
            os.remove(path)

    def test_empty_file_returns_defaults(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            path = f.name
        try:
            config = load_config(path)
            self.assertEqual(config, DEFAULTS)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
