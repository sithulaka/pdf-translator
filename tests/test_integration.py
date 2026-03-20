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
        from pdf_translator.extractor import extract_pdf_content
        from pdf_translator.engines import translate_text
        from pdf_translator.writer import save_as_text
        pdf_path = os.path.join(self.input_dir, 'test.pdf')
        output_path = os.path.join(self.output_dir, 'test.txt')
        os.makedirs(self.output_dir, exist_ok=True)
        pages_content = extract_pdf_content(pdf_path)
        self.assertTrue(len(pages_content) > 0)
        text, blocks, table_data = pages_content[0]
        self.assertIn("Hello", text)
        translated_texts = [translate_text(t) for t, _, _ in pages_content]
        self.assertTrue(all(isinstance(t, str) for t in translated_texts))
        save_as_text(output_path, pages_content, translated_texts, translate_text)
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("--- Page 1 ---", content)
        self.assertTrue(len(content) > 20)

    def test_cli_with_lang_flag(self):
        from pdf_translator.cli import parse_args
        args = parse_args(['--lang', 'ta', '--input', self.input_dir, '--output', self.output_dir])
        self.assertEqual(args.lang, 'ta')

    def test_process_pdfs_function(self):
        from main import process_pdfs
        from pdf_translator.config import DEFAULTS
        settings = dict(DEFAULTS)
        settings['input_folder'] = self.input_dir
        settings['output_folder'] = self.output_dir
        settings['force'] = True
        process_pdfs(settings)
        output_file = os.path.join(self.output_dir, 'test.txt')
        self.assertTrue(os.path.exists(output_file))

    def test_skip_already_translated(self):
        from main import process_pdfs
        from pdf_translator.config import DEFAULTS
        settings = dict(DEFAULTS)
        settings['input_folder'] = self.input_dir
        settings['output_folder'] = self.output_dir
        settings['force'] = True
        process_pdfs(settings)
        output_file = os.path.join(self.output_dir, 'test.txt')
        self.assertTrue(os.path.exists(output_file))
        first_mtime = os.path.getmtime(output_file)
        import time
        time.sleep(0.1)
        settings['force'] = False
        process_pdfs(settings)
        second_mtime = os.path.getmtime(output_file)
        self.assertEqual(first_mtime, second_mtime)


if __name__ == "__main__":
    unittest.main()
