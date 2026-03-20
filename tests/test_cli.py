import unittest
from pdf_translator.cli import parse_args, merge_args_with_config
from pdf_translator.config import DEFAULTS


class TestCLI(unittest.TestCase):
    def test_default_args(self):
        args = parse_args([])
        self.assertIsNone(args.lang)
        self.assertIsNone(args.input)
        self.assertFalse(args.force)

    def test_lang_flag(self):
        args = parse_args(['--lang', 'ta'])
        self.assertEqual(args.lang, 'ta')

    def test_short_flags(self):
        args = parse_args(['-l', 'en', '-i', 'docs/', '-o', 'out/'])
        self.assertEqual(args.lang, 'en')
        self.assertEqual(args.input, 'docs/')
        self.assertEqual(args.output, 'out/')

    def test_force_flag(self):
        args = parse_args(['--force'])
        self.assertTrue(args.force)

    def test_pages_flag(self):
        args = parse_args(['--pages', '1-5,8'])
        self.assertEqual(args.pages, '1-5,8')

    def test_merge_args_override_config(self):
        args = parse_args(['--lang', 'ta'])
        settings = merge_args_with_config(args, dict(DEFAULTS))
        self.assertEqual(settings['target_language'], 'ta')

    def test_merge_args_keep_config_defaults(self):
        args = parse_args([])
        settings = merge_args_with_config(args, dict(DEFAULTS))
        self.assertEqual(settings['target_language'], 'si')


if __name__ == "__main__":
    unittest.main()
