import unittest
import os
import fitz
from pdf_translator.tables import identify_tables, identify_tables_from_page, extract_tables_from_page


class TestIdentifyTablesFromPage(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.pdf_path = os.path.join(self.test_dir, 'test_table.pdf')

    def tearDown(self):
        if os.path.exists(self.pdf_path):
            os.remove(self.pdf_path)

    def test_page_with_no_tables(self):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Just text.")
        doc.save(self.pdf_path)
        doc.close()
        doc = fitz.open(self.pdf_path)
        page = doc.load_page(0)
        tables = identify_tables_from_page(page)
        doc.close()
        self.assertEqual(tables, [])

    def test_returns_list(self):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Some text")
        doc.save(self.pdf_path)
        doc.close()
        doc = fitz.open(self.pdf_path)
        page = doc.load_page(0)
        result = identify_tables_from_page(page)
        doc.close()
        self.assertIsInstance(result, list)


class TestIdentifyTablesFromBlocks(unittest.TestCase):
    def test_empty_blocks(self):
        self.assertEqual(identify_tables([]), [])

    def test_image_blocks_ignored(self):
        self.assertEqual(identify_tables([{'type': 1, 'image': b'fake'}]), [])


if __name__ == "__main__":
    unittest.main()
