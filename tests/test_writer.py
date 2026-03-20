import unittest
import os
from pdf_translator.writer import save_as_text, save_as_pdf, save_output


class TestSaveAsText(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_path = os.path.join(self.test_dir, 'test_output.txt')

    def tearDown(self):
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def _make_pages(self):
        return [("Original text here", [], [])]

    def test_creates_file(self):
        save_as_text(self.output_path, self._make_pages(), ["Translated text"], lambda x: x)
        self.assertTrue(os.path.exists(self.output_path))

    def test_contains_page_header(self):
        save_as_text(self.output_path, self._make_pages(), ["Translated text"], lambda x: x)
        with open(self.output_path, 'r') as f:
            content = f.read()
        self.assertIn("--- Page 1 ---", content)
        self.assertIn("Translated text", content)

    def test_bilingual_includes_original(self):
        save_as_text(self.output_path, self._make_pages(), ["Translated text"], lambda x: x, bilingual=True)
        with open(self.output_path, 'r') as f:
            content = f.read()
        self.assertIn("[Original]", content)
        self.assertIn("[Translated]", content)
        self.assertIn("Original text here", content)

    def test_non_bilingual_excludes_original(self):
        save_as_text(self.output_path, self._make_pages(), ["Translated text"], lambda x: x, bilingual=False)
        with open(self.output_path, 'r') as f:
            content = f.read()
        self.assertNotIn("[Original]", content)


class TestSaveAsPdf(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_path = os.path.join(self.test_dir, 'test_output.pdf')

    def tearDown(self):
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def _make_pages(self):
        return [("Original text here", [], [])]

    def test_creates_pdf_file(self):
        save_as_pdf(self.output_path, self._make_pages(), ["Translated text"])
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, 'rb') as f:
            self.assertEqual(f.read(5), b'%PDF-')

    def test_pdf_has_content(self):
        save_as_pdf(self.output_path, self._make_pages(), ["Translated text"])
        self.assertTrue(os.path.getsize(self.output_path) > 100)


class TestSaveOutput(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_path = os.path.join(self.test_dir, 'test_save_output.txt')

    def tearDown(self):
        base = os.path.splitext(self.base_path)[0]
        for ext in ('.txt', '.pdf'):
            path = base + ext
            if os.path.exists(path):
                os.remove(path)

    def _make_pages(self):
        return [("Original", [], [])]

    def test_txt_format(self):
        save_output(self.base_path, self._make_pages(), ["Translated"], lambda x: x, output_format='txt')
        base = os.path.splitext(self.base_path)[0]
        self.assertTrue(os.path.exists(base + '.txt'))

    def test_both_format(self):
        save_output(self.base_path, self._make_pages(), ["Translated"], lambda x: x, output_format='both')
        base = os.path.splitext(self.base_path)[0]
        self.assertTrue(os.path.exists(base + '.txt'))
        self.assertTrue(os.path.exists(base + '.pdf'))


if __name__ == "__main__":
    unittest.main()
