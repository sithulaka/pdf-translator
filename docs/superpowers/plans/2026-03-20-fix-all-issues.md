# PDF Translator - Fix All Issues Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 13 identified issues to make the PDF translator app fully functional.

**Architecture:** The app has two files — `main.py` (entry point) and `pdf_translator/translator.py` (core logic). Fixes are grouped into 4 tasks: 3 parallel agents (each touching a different file) + 1 sequential integration test.

**Tech Stack:** Python 3, PyMuPDF (fitz) 1.23.6, deep-translator 1.7.0

---

## File Structure

```
pdf_translator/
├── __init__.py          ← RENAME from inite.py
├── translator.py        ← MAJOR REWRITE (all functions)
main.py                  ← REWRITE (paths, input check, progress, error handling)
requirements.txt         ← CHANGE (remove reportlab)
tests/
├── __init__.py          ← CREATE
├── test_translator.py   ← CREATE
└── test_integration.py  ← CREATE
```

---

## Task 1: Fix Package Init & Unused Dependency (Agent 1)

**Files:**
- Delete: `pdf_translator/inite.py`
- Create: `pdf_translator/__init__.py`
- Modify: `requirements.txt`

Fixes issues: #1 (misnamed init), #10 (unused reportlab).

- [ ] **Step 1: Rename init file**

```bash
git mv pdf_translator/inite.py pdf_translator/__init__.py
```

- [ ] **Step 2: Remove unused reportlab from requirements.txt**

Edit `requirements.txt` to contain only:
```
pymupdf==1.23.6
deep-translator==1.7.0
```

- [ ] **Step 3: Verify import works**

```bash
python -c "from pdf_translator.translator import extract_pdf_content, translate_text; print('Import OK')"
```
Expected: `Import OK`

- [ ] **Step 4: Commit**

```bash
git add pdf_translator/__init__.py requirements.txt
git add -u pdf_translator/inite.py
git commit -m "fix: rename inite.py to __init__.py and remove unused reportlab dependency"
```

---

## Task 2: Rewrite translator.py — All Core Logic Fixes (Agent 2)

**Files:**
- Rewrite: `pdf_translator/translator.py`
- Create: `tests/__init__.py`
- Create: `tests/test_translator.py`

Fixes issues: #2 (5000 char limit), #3 (error handling in translator), #4 (wrong table detection), #5 (None return), #6 (tables not translated), #7 (PDF not closed), #12 (rate limiting with retry), #13 (translator instance reuse).

- [ ] **Step 1: Write tests**

Create `tests/__init__.py` (empty) and `tests/test_translator.py`:

```python
import unittest
from pdf_translator.translator import translate_text

class TestTranslateText(unittest.TestCase):
    def test_empty_text_returns_empty_string(self):
        """Issue #5: empty text should not crash."""
        result = translate_text("")
        self.assertEqual(result, "")

    def test_none_text_returns_empty_string(self):
        """Issue #5: None text should not crash."""
        result = translate_text(None)
        self.assertEqual(result, "")

    def test_whitespace_only_returns_empty_string(self):
        result = translate_text("   ")
        self.assertEqual(result, "")

    def test_short_text_translates(self):
        """Basic translation should return a non-empty string."""
        result = translate_text("Hello")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_long_text_does_not_crash(self):
        """Issue #2: text longer than 5000 chars must not crash."""
        long_text = "This is a test sentence. " * 300  # ~7500 chars
        result = translate_text(long_text)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_translator.py -v
```
Expected: Failures on empty/None tests.

- [ ] **Step 3: Rewrite `pdf_translator/translator.py` entirely**

Replace the entire file content with:

```python
import fitz  # PyMuPDF to handle PDF
import time
from deep_translator import GoogleTranslator

_translator_cache = {}
CHUNK_SIZE = 4500  # Under Google Translate's 5000 char limit
MAX_RETRIES = 3


def _get_translator(target_lang='si'):
    """Reuse translator instance per target language (Issue #13)."""
    if target_lang not in _translator_cache:
        _translator_cache[target_lang] = GoogleTranslator(source='auto', target=target_lang)
    return _translator_cache[target_lang]


def _translate_with_retry(translator, text):
    """Translate with exponential backoff retry on failure (Issue #12)."""
    for attempt in range(MAX_RETRIES):
        try:
            result = translator.translate(text)
            return result if result else ""
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                print(f"  Translation attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  Translation failed after {MAX_RETRIES} attempts: {e}. Using original text.")
                return text  # Fallback to original on final failure


def translate_text(text, target_lang='si'):
    """Translate text with chunking for large texts and error handling.

    Fixes: #2 (chunking), #3 (error handling), #5 (None/empty), #12 (retry), #13 (reuse).
    """
    if not text or not text.strip():
        return ""

    translator = _get_translator(target_lang)

    # Short text: translate directly
    if len(text) <= CHUNK_SIZE:
        return _translate_with_retry(translator, text)

    # Long text: chunk by paragraphs
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 1 > CHUNK_SIZE:
            if current_chunk:
                chunks.append(current_chunk)
            # Handle single paragraphs longer than CHUNK_SIZE
            while len(para) > CHUNK_SIZE:
                chunks.append(para[:CHUNK_SIZE])
                para = para[CHUNK_SIZE:]
            current_chunk = para
        else:
            current_chunk = current_chunk + '\n' + para if current_chunk else para

    if current_chunk:
        chunks.append(current_chunk)

    # Translate each chunk with rate limiting
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        translated_chunks.append(_translate_with_retry(translator, chunk))
        if i < len(chunks) - 1:
            time.sleep(0.5)  # Rate limiting between chunks

    return '\n'.join(translated_chunks)


def extract_pdf_content(pdf_path):
    """Extract text and blocks from each page of a PDF.

    Fixes: #7 (closes PDF document properly).
    """
    doc = fitz.open(pdf_path)
    pages = []

    try:
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            blocks = page.get_text("dict")['blocks']
            pages.append((text, blocks))
    finally:
        doc.close()

    return pages


def identify_tables(blocks):
    """Identify table-like structures from PDF blocks.

    Fixes: #4 (type 0 = text blocks, NOT type 1 which is images).
    Heuristic: text blocks with multiple lines where each line has
    multiple spans are likely table rows.
    """
    tables = []
    for block in blocks:
        if block.get('type') == 0 and 'lines' in block:  # Type 0 = text block
            lines = block['lines']
            if len(lines) >= 2:
                multi_span_lines = sum(1 for line in lines if len(line.get('spans', [])) > 1)
                if multi_span_lines >= 2:
                    table_data = []
                    for line in lines:
                        row = [span['text'] for span in line.get('spans', []) if span['text'].strip()]
                        if row:
                            table_data.append(row)
                    if table_data:
                        tables.append(table_data)
    return tables


def save_translated_text_as_file(file_path, pages_content, translated_texts):
    """Save translated content and tables to a text file.

    Fixes: #6 (tables are now translated too).
    """
    with open(file_path, 'w', encoding='utf-8') as file:
        for i, (original_text, blocks) in enumerate(pages_content):
            translated_text = translated_texts[i]

            file.write(f"--- Page {i + 1} ---\n")
            file.write(translated_text + "\n")
            file.write("\n")

            # Translate and write tables
            tables = identify_tables(blocks)
            for table_data in tables:
                for row in table_data:
                    translated_row = [translate_text(cell) for cell in row]
                    file.write(" | ".join(translated_row) + "\n")
                file.write("\n")

            file.write("\n\n")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_translator.py -v
```
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add pdf_translator/translator.py tests/__init__.py tests/test_translator.py
git commit -m "fix: rewrite translator with chunking, retry, table fix, PDF cleanup, and error handling"
```

---

## Task 3: Fix main.py — Paths, Input Check, Progress & Error Handling (Agent 3)

**Files:**
- Rewrite: `main.py`

Fixes issues: #3 (error handling in main), #8 (relative paths), #9 (input folder check), #11 (progress feedback).

- [ ] **Step 1: Rewrite main.py**

Replace the entire content of `main.py`:

```python
import os
import sys
from pdf_translator.translator import extract_pdf_content, translate_text, save_translated_text_as_file

def process_pdfs(input_folder, output_folder):
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        sys.exit(1)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in '{input_folder}'.")
        return

    total_files = len(pdf_files)
    print(f"Found {total_files} PDF file(s) to process.\n")

    for file_idx, file_name in enumerate(pdf_files, 1):
        pdf_path = os.path.join(input_folder, file_name)
        output_file_path = os.path.join(output_folder, file_name.rsplit('.', 1)[0] + '.txt')

        print(f"[{file_idx}/{total_files}] Processing: {file_name}")

        try:
            # Extract content from the PDF
            pages_content = extract_pdf_content(pdf_path)
            print(f"  Extracted {len(pages_content)} page(s)")

            # Translate the content
            translated_texts = []
            for page_num, (text, _) in enumerate(pages_content, 1):
                print(f"  Translating page {page_num}/{len(pages_content)}...")
                translated_texts.append(translate_text(text))

            # Save the translated content to a text file
            save_translated_text_as_file(output_file_path, pages_content, translated_texts)
            print(f"  Saved: {output_file_path}\n")

        except Exception as e:
            print(f"  Error processing '{file_name}': {e}\n")
            continue

    print("Done.")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(base_dir, 'input_pdfs')
    output_folder = os.path.join(base_dir, 'output_texts')
    process_pdfs(input_folder, output_folder)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify syntax**

```bash
python -c "import py_compile; py_compile.compile('main.py', doraise=True); print('Syntax OK')"
```
Expected: `Syntax OK`

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "fix: add error handling, absolute paths, input validation, and progress output"
```

---

## Task 4: Integration Test (Agent 4 — runs AFTER Tasks 1-3)

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Create integration test file**

Create `tests/test_integration.py`:

```python
import unittest
import os
import fitz

class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Create a minimal test PDF."""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(self.test_dir)
        self.input_dir = os.path.join(self.project_dir, 'test_input')
        self.output_dir = os.path.join(self.project_dir, 'test_output')
        os.makedirs(self.input_dir, exist_ok=True)

        # Create a simple test PDF
        pdf_path = os.path.join(self.input_dir, 'test.pdf')
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello World. This is a test document.")
        doc.save(pdf_path)
        doc.close()

    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.input_dir):
            shutil.rmtree(self.input_dir)
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_full_pipeline(self):
        """Test the complete extract -> translate -> save pipeline."""
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
        """Test the main process_pdfs function."""
        from main import process_pdfs

        process_pdfs(self.input_dir, self.output_dir)

        output_file = os.path.join(self.output_dir, 'test.txt')
        self.assertTrue(os.path.exists(output_file))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run all tests**

```bash
python -m pytest tests/ -v
```
Expected: All PASS.

- [ ] **Step 3: Run the actual app end-to-end**

```bash
python main.py
```
Expected: Processes any PDFs in `input_pdfs/`, prints progress, saves output to `output_texts/`.

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for full translation pipeline"
```

---

## Parallel Execution Strategy

```
┌──────────────────────────────────────────────┐
│           PARALLEL (Agents 1-3)              │
│                                              │
│  Agent 1: Task 1 (init file + requirements)  │
│  Agent 2: Task 2 (translator.py rewrite)     │
│  Agent 3: Task 3 (main.py rewrite)           │
│                                              │
│  Each agent touches DIFFERENT files only.    │
│  No merge conflicts possible.               │
│                                              │
└──────────────────┬───────────────────────────┘
                   │ all complete
                   ▼
┌──────────────────────────────────────────────┐
│        SEQUENTIAL (Agent 4)                  │
│  Agent 4: Task 4 (integration test)          │
└──────────────────────────────────────────────┘
```

Tasks 1-3 are fully independent (each touches different files) and run in parallel.
Task 4 depends on all others completing first.

## Issues Coverage Map

| Issue | Description | Fixed In |
|-------|-------------|----------|
| #1  | `inite.py` misnamed | Task 1 |
| #2  | 5000 char limit | Task 2 |
| #3  | No error handling | Task 2 + Task 3 |
| #4  | Wrong table detection | Task 2 |
| #5  | `translate_text()` returns None | Task 2 |
| #6  | Tables not translated | Task 2 |
| #7  | PDF not closed | Task 2 |
| #8  | Relative paths | Task 3 |
| #9  | No input folder check | Task 3 |
| #10 | Unused reportlab | Task 1 |
| #11 | No progress feedback | Task 3 |
| #12 | No rate limiting/retry | Task 2 |
| #13 | New translator per call | Task 2 |
