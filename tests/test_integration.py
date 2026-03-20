import unittest
import os
import fitz

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(self.test_dir)
        self.input_dir = os.path.join(self.project_dir, 'test_input')
        self.output_dir = os.path.join(self.project_dir, 'test_output')
        os.makedirs(self.input_dir, exist_ok=True)

        pdf_path = os.path.join(self.input_dir, 'test.pdf')
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello World. This is a test document.")
        doc.save(pdf_path)
        doc.close()

    def tearDown(self):
        import shutil
        if os.path.exists(self.input_dir):
            shutil.rmtree(self.input_dir)
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_full_pipeline(self):
        from pdf_translator.translator import extract_pdf_content, translate_text, save_translated_text_as_file

        pdf_path = os.path.join(self.input_dir, 'test.pdf')
        output_path = os.path.join(self.output_dir, 'test.txt')
        os.makedirs(self.output_dir, exist_ok=True)

        pages_content = extract_pdf_content(pdf_path)
        self.assertTrue(len(pages_content) > 0)

        text, blocks = pages_content[0]
        self.assertIn("Hello", text)

        translated_texts = [translate_text(t) for t, _ in pages_content]
        self.assertTrue(all(isinstance(t, str) for t in translated_texts))

        save_translated_text_as_file(output_path, pages_content, translated_texts)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("--- Page 1 ---", content)
        self.assertTrue(len(content) > 20)

    def test_process_pdfs_function(self):
        from main import process_pdfs
        process_pdfs(self.input_dir, self.output_dir)
        output_file = os.path.join(self.output_dir, 'test.txt')
        self.assertTrue(os.path.exists(output_file))

if __name__ == "__main__":
    unittest.main()
