import unittest
import os
import fitz
from pdf_translator.extractor import extract_pdf_content, parse_page_range


class TestParsePageRange(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(parse_page_range(None))

    def test_empty_returns_none(self):
        self.assertIsNone(parse_page_range(''))

    def test_single_page(self):
        self.assertEqual(parse_page_range('3'), {2})

    def test_range(self):
        self.assertEqual(parse_page_range('1-3'), {0, 1, 2})

    def test_mixed(self):
        self.assertEqual(parse_page_range('1,3,5-7'), {0, 2, 4, 5, 6})


class TestExtractPdfContent(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.pdf_path = os.path.join(self.test_dir, 'test_extract.pdf')
        doc = fitz.open()
        page1 = doc.new_page()
        page1.insert_text((72, 72), "Page one content")
        page2 = doc.new_page()
        page2.insert_text((72, 72), "Page two content")
        doc.save(self.pdf_path)
        doc.close()

    def tearDown(self):
        if os.path.exists(self.pdf_path):
            os.remove(self.pdf_path)

    def test_extract_all_pages(self):
        pages = extract_pdf_content(self.pdf_path)
        self.assertEqual(len(pages), 2)
        self.assertIn("Page one", pages[0][0])
        self.assertIn("Page two", pages[1][0])

    def test_extract_page_range(self):
        pages = extract_pdf_content(self.pdf_path, page_range={0})
        self.assertEqual(len(pages), 1)
        self.assertIn("Page one", pages[0][0])

    def test_returns_three_tuple(self):
        pages = extract_pdf_content(self.pdf_path)
        text, blocks, table_data = pages[0]
        self.assertIsInstance(text, str)
        self.assertIsInstance(blocks, list)
        self.assertIsInstance(table_data, list)


if __name__ == "__main__":
    unittest.main()
