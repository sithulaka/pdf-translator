# PDF Translator — All 15 Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all 15 improvements from IMPROVEMENTS.md — CLI, OCR, PDF output, logging, caching, concurrency, multiple engines, and more.

**Architecture:** Phase 1 restructures the monolithic `translator.py` into separate modules (`extractor.py`, `engines.py`, `cache.py`, `writer.py`, `tables.py`) and adds CLI + logging as the foundation. Phase 2 dispatches 5 parallel agents, each working on a different new module file with zero conflicts. Phase 3 wires everything together in `main.py` with concurrency, progress bar, batch summary, and config file support.

**Tech Stack:** Python 3, PyMuPDF 1.23.6, deep-translator 1.7.0, pytesseract, Pillow, fpdf2, tqdm, pyyaml

---

## File Structure (Final State)

```
pdf_translator/
├── __init__.py              ← UPDATE: export public API
├── cli.py                   ← CREATE: argparse CLI parsing
├── extractor.py             ← CREATE: PDF extraction + OCR + password support
├── engines.py               ← CREATE: translation engines (Google, MyMemory, DeepL) + chunking + retry
├── cache.py                 ← CREATE: disk-based translation cache
├── tables.py                ← CREATE: table detection using page.find_tables()
├── writer.py                ← CREATE: output writers (txt, pdf, bilingual)
├── config.py                ← CREATE: config file loading + defaults
main.py                      ← REWRITE: orchestrator with concurrency, progress, batch summary
requirements.txt              ← UPDATE: add new dependencies
config.default.yaml           ← CREATE: default config template
tests/
├── __init__.py
├── test_cli.py              ← CREATE
├── test_extractor.py        ← CREATE
├── test_engines.py          ← CREATE (rename from test_translator.py)
├── test_cache.py            ← CREATE
├── test_tables.py           ← CREATE
├── test_writer.py           ← CREATE
├── test_config.py           ← CREATE
└── test_integration.py      ← UPDATE
```

---

## Phase 1: Foundation — Restructure + CLI + Logging (Sequential)

### Task 1: Restructure into modules + CLI + Logging

This task splits `translator.py` into separate module files, adds CLI with argparse, and replaces all `print()` with `logging`. This is the foundation for all parallel work in Phase 2.

**Files:**
- Create: `pdf_translator/cli.py`
- Create: `pdf_translator/extractor.py`
- Create: `pdf_translator/engines.py`
- Create: `pdf_translator/tables.py`
- Create: `pdf_translator/writer.py`
- Create: `pdf_translator/cache.py`
- Create: `pdf_translator/config.py`
- Modify: `pdf_translator/__init__.py`
- Modify: `main.py`
- Modify: `requirements.txt`
- Create: `config.default.yaml`
- Create: `tests/test_cli.py`

**Improvements covered:** #1 (CLI), #4 (Logging) — partial foundation for all others.

- [ ] **Step 1: Update requirements.txt**

```
pymupdf==1.23.6
deep-translator==1.7.0
pytesseract>=0.3.10
Pillow>=10.0.0
fpdf2>=2.7.0
tqdm>=4.66.0
pyyaml>=6.0
```

- [ ] **Step 2: Create `config.default.yaml`**

```yaml
target_language: si
input_folder: input_pdfs
output_folder: output_texts
output_format: txt
engine: google
max_workers: 3
bilingual: false
```

- [ ] **Step 3: Create `pdf_translator/config.py`**

```python
import os
import yaml
import logging

logger = logging.getLogger(__name__)

DEFAULTS = {
    'target_language': 'si',
    'input_folder': 'input_pdfs',
    'output_folder': 'output_texts',
    'output_format': 'txt',
    'engine': 'google',
    'max_workers': 3,
    'bilingual': False,
}


def load_config(config_path=None):
    """Load config from YAML file, falling back to defaults."""
    config = dict(DEFAULTS)

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f) or {}
        config.update(file_config)
        logger.debug("Loaded config from %s", config_path)
    elif config_path:
        logger.warning("Config file not found: %s, using defaults", config_path)

    return config
```

- [ ] **Step 4: Create `pdf_translator/cli.py`**

```python
import argparse
import logging
import os


def parse_args(argv=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='PDF Translator — Extract text from PDFs and translate to any language.'
    )
    parser.add_argument('--input', '-i', default=None,
                        help='Input folder containing PDF files (default: input_pdfs)')
    parser.add_argument('--output', '-o', default=None,
                        help='Output folder for translated files (default: output_texts)')
    parser.add_argument('--lang', '-l', default=None,
                        help='Target language code, e.g. si, ta, en (default: si)')
    parser.add_argument('--format', '-f', choices=['txt', 'pdf', 'both'], default=None,
                        help='Output format (default: txt)')
    parser.add_argument('--engine', '-e', choices=['google', 'mymemory'], default=None,
                        help='Translation engine (default: google)')
    parser.add_argument('--api-key', default=None,
                        help='API key for translation engines that require one')
    parser.add_argument('--pages', default=None,
                        help='Page range to translate, e.g. "1-5" or "3,7,10-15"')
    parser.add_argument('--password', default=None,
                        help='Password for encrypted PDFs')
    parser.add_argument('--bilingual', action='store_true', default=None,
                        help='Include original text alongside translation')
    parser.add_argument('--force', action='store_true', default=False,
                        help='Re-translate even if output already exists')
    parser.add_argument('--workers', type=int, default=None,
                        help='Number of concurrent translation workers (default: 3)')
    parser.add_argument('--config', default=None,
                        help='Path to config YAML file')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                        help='Enable debug logging')
    parser.add_argument('--quiet', '-q', action='store_true', default=False,
                        help='Only show warnings and errors')
    parser.add_argument('--log', default=None,
                        help='Write logs to file')

    return parser.parse_args(argv)


def setup_logging(verbose=False, quiet=False, log_file=None):
    """Configure logging based on CLI flags."""
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.WARNING
    else:
        level = logging.INFO

    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        datefmt='%H:%M:%S',
        handlers=handlers,
    )


def merge_args_with_config(args, config):
    """CLI args override config file values. Returns final settings dict."""
    base_dir = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    settings = dict(config)
    if args.input is not None:
        settings['input_folder'] = args.input
    if args.output is not None:
        settings['output_folder'] = args.output
    if args.lang is not None:
        settings['target_language'] = args.lang
    if args.format is not None:
        settings['output_format'] = args.format
    if args.engine is not None:
        settings['engine'] = args.engine
    if args.api_key is not None:
        settings['api_key'] = args.api_key
    if args.pages is not None:
        settings['pages'] = args.pages
    if args.password is not None:
        settings['password'] = args.password
    if args.bilingual is not None:
        settings['bilingual'] = args.bilingual
    if args.workers is not None:
        settings['max_workers'] = args.workers
    settings['force'] = args.force

    # Resolve paths relative to script location
    for key in ('input_folder', 'output_folder'):
        if not os.path.isabs(settings[key]):
            settings[key] = os.path.join(base_dir, settings[key])

    return settings
```

- [ ] **Step 5: Create `pdf_translator/extractor.py` (skeleton)**

Move `extract_pdf_content` here. OCR + password will be added by Phase 2 agent.

```python
import fitz
import logging

logger = logging.getLogger(__name__)


def extract_pdf_content(pdf_path, password=None, page_range=None):
    """Extract text, blocks, and table data from each page of a PDF.

    Args:
        pdf_path: Path to the PDF file.
        password: Optional password for encrypted PDFs.
        page_range: Optional set of page numbers (0-indexed) to extract.

    Returns:
        List of (text, blocks, table_data) tuples per page.
        table_data is extracted while doc is open (page objects invalid after close).
    """
    from pdf_translator.tables import extract_tables_from_page

    doc = fitz.open(pdf_path)
    pages = []

    try:
        if doc.is_encrypted:
            if password:
                if not doc.authenticate(password):
                    raise ValueError(f"Wrong password for '{pdf_path}'")
            else:
                raise ValueError(f"PDF '{pdf_path}' is encrypted. Use --password flag.")

        for page_num in range(doc.page_count):
            if page_range is not None and page_num not in page_range:
                continue

            page = doc.load_page(page_num)
            text = page.get_text("text")
            blocks = page.get_text("dict")['blocks']
            # Extract tables while page is still valid
            table_data = extract_tables_from_page(page, blocks)
            pages.append((text, blocks, table_data))
    finally:
        doc.close()

    logger.debug("Extracted %d page(s) from %s", len(pages), pdf_path)
    return pages


def parse_page_range(page_str):
    """Parse page range string like '1-5' or '3,7,10-15' into a set of 0-indexed page numbers."""
    if not page_str:
        return None

    pages = set()
    for part in page_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            pages.update(range(int(start) - 1, int(end)))
        else:
            pages.add(int(part) - 1)

    return pages
```

- [ ] **Step 6: Create `pdf_translator/engines.py` (skeleton)**

Move `translate_text`, `_get_translator`, `_translate_with_retry` here. Multiple engines will be added by Phase 2 agent.

```python
import time
import logging
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

_translator_cache = {}
CHUNK_SIZE = 4500
MAX_RETRIES = 3


def create_engine(engine_name='google', target_lang='si', api_key=None):
    """Create a translator engine instance."""
    cache_key = f"{engine_name}:{target_lang}"
    if cache_key not in _translator_cache:
        if engine_name == 'google':
            _translator_cache[cache_key] = GoogleTranslator(source='auto', target=target_lang)
        else:
            raise ValueError(f"Unknown engine: {engine_name}. Available: google")

    return _translator_cache[cache_key]


def _translate_with_retry(translator, text):
    """Translate with exponential backoff retry on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            result = translator.translate(text)
            return result if result else ""
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = (2 ** attempt) * 0.5
                logger.warning("Translation attempt %d failed: %s. Retrying in %.1fs...",
                               attempt + 1, e, wait_time)
                time.sleep(wait_time)
            else:
                logger.error("Translation failed after %d attempts: %s. Using original text.",
                             MAX_RETRIES, e)
                return text


def translate_text(text, target_lang='si', engine_name='google', api_key=None):
    """Translate text with chunking for large texts and error handling."""
    if not text or not text.strip():
        return ""

    translator = create_engine(engine_name, target_lang, api_key)

    if len(text) <= CHUNK_SIZE:
        return _translate_with_retry(translator, text)

    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 1 > CHUNK_SIZE:
            if current_chunk:
                chunks.append(current_chunk)
            while len(para) > CHUNK_SIZE:
                chunks.append(para[:CHUNK_SIZE])
                para = para[CHUNK_SIZE:]
            current_chunk = para
        else:
            current_chunk = current_chunk + '\n' + para if current_chunk else para

    if current_chunk:
        chunks.append(current_chunk)

    translated_chunks = []
    for i, chunk in enumerate(chunks):
        translated_chunks.append(_translate_with_retry(translator, chunk))
        if i < len(chunks) - 1:
            time.sleep(0.5)

    return '\n'.join(translated_chunks)
```

- [ ] **Step 7: Create `pdf_translator/tables.py` (skeleton)**

Move `identify_tables` here. Better detection will be added by Phase 2 agent.

```python
import logging

logger = logging.getLogger(__name__)


def identify_tables(blocks):
    """Identify table-like structures from PDF blocks.

    Placeholder — Phase 2 agent will replace with page.find_tables().
    """
    tables = []
    for block in blocks:
        if block.get('type') == 0 and 'lines' in block:
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
```

- [ ] **Step 8: Create `pdf_translator/writer.py` (skeleton)**

Move `save_translated_text_as_file` here. PDF output + bilingual will be added by Phase 2 agent.

```python
import logging

logger = logging.getLogger(__name__)


def save_as_text(file_path, pages_content, translated_texts, translate_fn,
                 bilingual=False):
    """Save translated content to a text file.

    pages_content is a list of (text, blocks, table_data) tuples.
    table_data is pre-extracted by extractor.py while the doc was open.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for i, (original_text, blocks, table_data) in enumerate(pages_content):
            translated_text = translated_texts[i]

            f.write(f"--- Page {i + 1} ---\n")

            if bilingual:
                f.write("[Original]\n")
                f.write(original_text + "\n\n")
                f.write("[Translated]\n")

            f.write(translated_text + "\n\n")

            for table in table_data:
                for row in table:
                    translated_row = [translate_fn(cell) for cell in row]
                    f.write(" | ".join(translated_row) + "\n")
                f.write("\n")

            f.write("\n")

    logger.info("Saved text output: %s", file_path)
```

- [ ] **Step 9: Create `pdf_translator/cache.py` (skeleton)**

```python
import hashlib
import json
import os
import logging

logger = logging.getLogger(__name__)

CACHE_FILE = '.translation_cache.json'


def _get_cache_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', CACHE_FILE)


def load_cache():
    """Load translation cache from disk."""
    path = _get_cache_path()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """Save translation cache to disk."""
    path = _get_cache_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_cache_key(text, target_lang):
    """Generate cache key for a text + language pair."""
    return hashlib.md5(f"{target_lang}:{text}".encode()).hexdigest()
```

- [ ] **Step 10: Update `pdf_translator/__init__.py`**

```python
from pdf_translator.engines import translate_text
from pdf_translator.extractor import extract_pdf_content
from pdf_translator.writer import save_as_text
from pdf_translator.tables import identify_tables
```

- [ ] **Step 11: Rewrite `main.py` — minimal orchestrator with CLI**

```python
import os
import sys
import logging
from pdf_translator.cli import parse_args, setup_logging, merge_args_with_config
from pdf_translator.config import load_config
from pdf_translator.extractor import extract_pdf_content, parse_page_range
from pdf_translator.engines import translate_text
from pdf_translator.writer import save_as_text

logger = logging.getLogger(__name__)


def process_pdfs(settings):
    input_folder = settings['input_folder']
    output_folder = settings['output_folder']
    target_lang = settings['target_language']
    engine_name = settings.get('engine', 'google')
    api_key = settings.get('api_key')
    password = settings.get('password')
    force = settings.get('force', False)
    bilingual = settings.get('bilingual', False)
    page_range = parse_page_range(settings.get('pages'))

    if not os.path.exists(input_folder):
        logger.error("Input folder '%s' does not exist.", input_folder)
        sys.exit(1)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]

    if not pdf_files:
        logger.info("No PDF files found in '%s'.", input_folder)
        return

    total_files = len(pdf_files)
    logger.info("Found %d PDF file(s) to process.\n", total_files)

    for file_idx, file_name in enumerate(pdf_files, 1):
        pdf_path = os.path.join(input_folder, file_name)
        output_file_path = os.path.join(output_folder, file_name.rsplit('.', 1)[0] + '.txt')

        # Skip already translated
        if not force and os.path.exists(output_file_path):
            input_mtime = os.path.getmtime(pdf_path)
            output_mtime = os.path.getmtime(output_file_path)
            if output_mtime > input_mtime:
                logger.info("[%d/%d] Skipping (already translated): %s",
                            file_idx, total_files, file_name)
                continue

        logger.info("[%d/%d] Processing: %s", file_idx, total_files, file_name)

        try:
            pages_content = extract_pdf_content(pdf_path, password=password,
                                                 page_range=page_range)
            logger.info("  Extracted %d page(s)", len(pages_content))

            translated_texts = []
            for page_num, (text, _blocks, _tables) in enumerate(pages_content, 1):
                logger.info("  Translating page %d/%d...", page_num, len(pages_content))
                translated_texts.append(
                    translate_text(text, target_lang=target_lang,
                                   engine_name=engine_name, api_key=api_key)
                )

            translate_fn = lambda cell: translate_text(
                cell, target_lang=target_lang,
                engine_name=engine_name, api_key=api_key
            )

            save_as_text(output_file_path, pages_content, translated_texts,
                         translate_fn, bilingual=bilingual)
            logger.info("  Saved: %s\n", output_file_path)

        except Exception as e:
            logger.error("  Error processing '%s': %s\n", file_name, e)
            continue

    logger.info("Done.")


def main():
    args = parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, log_file=args.log)

    config = load_config(args.config)
    settings = merge_args_with_config(args, config)

    process_pdfs(settings)


if __name__ == "__main__":
    main()
```

- [ ] **Step 12: Create `tests/test_cli.py`**

```python
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
```

- [ ] **Step 13: Run tests**

```bash
cd /home/ceylond/Desktop/work/pdf-translator && source venv/bin/activate && pip install pyyaml tqdm fpdf2 -q && python -m pytest tests/test_cli.py -v
```
Expected: All PASS.

- [ ] **Step 14: Create `tests/test_config.py`**

```python
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
            # Non-overridden defaults preserved
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
```

- [ ] **Step 15: Delete the old `pdf_translator/translator.py`**

Remove the old monolithic file now that everything has been split:

```bash
rm pdf_translator/translator.py
```

- [ ] **Step 16: Update `tests/test_integration.py`** to use new imports

Replace imports from `pdf_translator.translator` with new module imports:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 17: Remove old `tests/test_translator.py`**

```bash
rm tests/test_translator.py
```

- [ ] **Step 18: Run all tests**

```bash
python -m pytest tests/ -v
```
Expected: All PASS.

- [ ] **Step 19: Commit**

```bash
git add -A
git commit -m "refactor: split translator.py into modules, add CLI with argparse and logging"
```

---

## Phase 2: Feature Implementation (5 Parallel Agents)

Each agent works on a DIFFERENT file — zero merge conflicts.

---

### Task 2: OCR Support in `extractor.py` (Agent A)

**Files:**
- Modify: `pdf_translator/extractor.py`
- Create: `tests/test_extractor.py`

**Improvements covered:** #2 (OCR), #9 (page range — already wired), #15 (password — already wired).

- [ ] **Step 1: Write tests**

Create `tests/test_extractor.py`:

```python
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

    def test_ocr_fallback_on_image_page(self):
        """Create a PDF with an image page (no text layer) and verify OCR runs."""
        img_pdf_path = os.path.join(self.test_dir, 'test_image.pdf')
        doc = fitz.open()
        page = doc.new_page()
        # Insert a simple rectangle as image content — no text layer
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(50, 50, 200, 100))
        shape.finish(color=(0, 0, 0))
        shape.commit()
        doc.save(img_pdf_path)
        doc.close()

        try:
            pages = extract_pdf_content(img_pdf_path)
            # Should not crash — OCR may or may not find text in the rectangle
            self.assertEqual(len(pages), 1)
            self.assertIsInstance(pages[0][0], str)
        finally:
            os.remove(img_pdf_path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests — expect OCR test may fail**

```bash
python -m pytest tests/test_extractor.py -v
```

- [ ] **Step 3: Add OCR fallback to `extract_pdf_content` in `pdf_translator/extractor.py`**

Replace the function:

```python
import fitz
import logging

logger = logging.getLogger(__name__)

# OCR is optional — graceful fallback if not installed
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.debug("pytesseract/Pillow not installed — OCR disabled")


def extract_pdf_content(pdf_path, password=None, page_range=None):
    """Extract text, blocks, and table data from each page of a PDF.

    Falls back to OCR for pages with no extractable text.
    Table data is extracted while doc is open (page objects are invalid after close).
    """
    from pdf_translator.tables import extract_tables_from_page

    doc = fitz.open(pdf_path)
    pages = []

    try:
        if doc.is_encrypted:
            if password:
                if not doc.authenticate(password):
                    raise ValueError(f"Wrong password for '{pdf_path}'")
            else:
                raise ValueError(f"PDF '{pdf_path}' is encrypted. Use --password flag.")

        for page_num in range(doc.page_count):
            if page_range is not None and page_num not in page_range:
                continue

            page = doc.load_page(page_num)
            text = page.get_text("text")
            blocks = page.get_text("dict")['blocks']

            # OCR fallback for image-only pages
            if not text.strip() and OCR_AVAILABLE:
                logger.info("  Page %d has no text — running OCR...", page_num + 1)
                try:
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    text = pytesseract.image_to_string(img)
                except Exception as e:
                    logger.warning("  OCR failed on page %d: %s", page_num + 1, e)
                    text = ""

            # Extract tables while page is still valid
            table_data = extract_tables_from_page(page, blocks)
            pages.append((text, blocks, table_data))
    finally:
        doc.close()

    logger.debug("Extracted %d page(s) from %s", len(pages), pdf_path)
    return pages


def parse_page_range(page_str):
    """Parse page range string like '1-5' or '3,7,10-15' into a set of 0-indexed page numbers."""
    if not page_str:
        return None

    pages = set()
    for part in page_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            pages.update(range(int(start) - 1, int(end)))
        else:
            pages.add(int(part) - 1)

    return pages
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_extractor.py -v
```
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add pdf_translator/extractor.py tests/test_extractor.py
git commit -m "feat: add OCR fallback for scanned PDFs and password support"
```

---

### Task 3: Multiple Translation Engines in `engines.py` (Agent B)

**Files:**
- Modify: `pdf_translator/engines.py`
- Create: `tests/test_engines.py`

**Improvements covered:** #8 (multiple engines).

- [ ] **Step 1: Write tests**

Create `tests/test_engines.py`:

```python
import unittest
from pdf_translator.engines import translate_text, create_engine


class TestTranslateText(unittest.TestCase):
    def test_empty_text_returns_empty_string(self):
        self.assertEqual(translate_text(""), "")

    def test_none_text_returns_empty_string(self):
        self.assertEqual(translate_text(None), "")

    def test_whitespace_only_returns_empty_string(self):
        self.assertEqual(translate_text("   "), "")

    def test_short_text_translates(self):
        result = translate_text("Hello")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_long_text_does_not_crash(self):
        long_text = "This is a test sentence. " * 300
        result = translate_text(long_text)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_google_engine(self):
        result = translate_text("Hello", engine_name='google')
        self.assertIsInstance(result, str)

    def test_mymemory_engine(self):
        result = translate_text("Hello", engine_name='mymemory')
        self.assertIsInstance(result, str)

    def test_unknown_engine_raises(self):
        with self.assertRaises(ValueError):
            create_engine('nonexistent', 'si')


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add MyMemory engine to `pdf_translator/engines.py`**

Update the `create_engine` function:

```python
import time
import logging
from deep_translator import GoogleTranslator, MyMemoryTranslator

logger = logging.getLogger(__name__)

_translator_cache = {}
CHUNK_SIZE = 4500
MAX_RETRIES = 3

SUPPORTED_ENGINES = ['google', 'mymemory']


def create_engine(engine_name='google', target_lang='si', api_key=None):
    """Create a translator engine instance."""
    cache_key = f"{engine_name}:{target_lang}"
    if cache_key not in _translator_cache:
        if engine_name == 'google':
            _translator_cache[cache_key] = GoogleTranslator(source='auto', target=target_lang)
        elif engine_name == 'mymemory':
            _translator_cache[cache_key] = MyMemoryTranslator(source='auto', target=target_lang)
        else:
            raise ValueError(
                f"Unknown engine: '{engine_name}'. Available: {', '.join(SUPPORTED_ENGINES)}"
            )

    return _translator_cache[cache_key]


def _translate_with_retry(translator, text):
    """Translate with exponential backoff retry on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            result = translator.translate(text)
            return result if result else ""
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = (2 ** attempt) * 0.5
                logger.warning("Translation attempt %d failed: %s. Retrying in %.1fs...",
                               attempt + 1, e, wait_time)
                time.sleep(wait_time)
            else:
                logger.error("Translation failed after %d attempts: %s. Using original text.",
                             MAX_RETRIES, e)
                return text


def translate_text(text, target_lang='si', engine_name='google', api_key=None):
    """Translate text with chunking for large texts and error handling."""
    if not text or not text.strip():
        return ""

    translator = create_engine(engine_name, target_lang, api_key)

    if len(text) <= CHUNK_SIZE:
        return _translate_with_retry(translator, text)

    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 1 > CHUNK_SIZE:
            if current_chunk:
                chunks.append(current_chunk)
            while len(para) > CHUNK_SIZE:
                chunks.append(para[:CHUNK_SIZE])
                para = para[CHUNK_SIZE:]
            current_chunk = para
        else:
            current_chunk = current_chunk + '\n' + para if current_chunk else para

    if current_chunk:
        chunks.append(current_chunk)

    translated_chunks = []
    for i, chunk in enumerate(chunks):
        translated_chunks.append(_translate_with_retry(translator, chunk))
        if i < len(chunks) - 1:
            time.sleep(0.5)

    return '\n'.join(translated_chunks)
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_engines.py -v
```
Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add pdf_translator/engines.py tests/test_engines.py
git commit -m "feat: add MyMemory translation engine support"
```

---

### Task 4: Translation Cache in `cache.py` (Agent C)

**Files:**
- Modify: `pdf_translator/cache.py`
- Create: `tests/test_cache.py`

**Improvements covered:** #7 (translation cache).

- [ ] **Step 1: Write tests**

Create `tests/test_cache.py`:

```python
import unittest
import os
import json
from pdf_translator.cache import load_cache, save_cache, get_cache_key, CachedTranslator


class TestCacheKey(unittest.TestCase):
    def test_same_input_same_key(self):
        k1 = get_cache_key("hello", "si")
        k2 = get_cache_key("hello", "si")
        self.assertEqual(k1, k2)

    def test_different_text_different_key(self):
        k1 = get_cache_key("hello", "si")
        k2 = get_cache_key("world", "si")
        self.assertNotEqual(k1, k2)

    def test_different_lang_different_key(self):
        k1 = get_cache_key("hello", "si")
        k2 = get_cache_key("hello", "ta")
        self.assertNotEqual(k1, k2)


class TestCacheIO(unittest.TestCase):
    def setUp(self):
        self.cache_path = os.path.join(os.path.dirname(__file__), 'test_cache.json')

    def tearDown(self):
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)

    def test_save_and_load(self):
        data = {"key1": "value1", "key2": "value2"}
        save_cache(data, self.cache_path)
        loaded = load_cache(self.cache_path)
        self.assertEqual(loaded, data)

    def test_load_missing_file(self):
        loaded = load_cache('/nonexistent/path.json')
        self.assertEqual(loaded, {})


class TestCachedTranslator(unittest.TestCase):
    def setUp(self):
        self.cache_path = os.path.join(os.path.dirname(__file__), 'test_ct_cache.json')
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
        result = self.ct.translate("hello", target_lang='si')
        self.assertEqual(result, "translated:hello")
        self.assertEqual(self.call_count, 1)  # NOT called again

    def test_different_text_translates_again(self):
        self.ct.translate("hello", target_lang='si')
        self.ct.translate("world", target_lang='si')
        self.assertEqual(self.call_count, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests — expect failures**

```bash
python -m pytest tests/test_cache.py -v
```

- [ ] **Step 3: Implement full cache in `pdf_translator/cache.py`**

```python
import hashlib
import json
import os
import logging

logger = logging.getLogger(__name__)

CACHE_FILE = '.translation_cache.json'


def _default_cache_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', CACHE_FILE)


def load_cache(path=None):
    """Load translation cache from disk."""
    path = path or _default_cache_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to load cache: %s", e)
    return {}


def save_cache(cache, path=None):
    """Save translation cache to disk."""
    path = path or _default_cache_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.warning("Failed to save cache: %s", e)


def get_cache_key(text, target_lang):
    """Generate cache key for a text + language pair."""
    return hashlib.md5(f"{target_lang}:{text}".encode()).hexdigest()


class CachedTranslator:
    """Wraps a translate function with disk-backed caching."""

    def __init__(self, translate_fn, cache_path=None):
        self._translate_fn = translate_fn
        self._cache_path = cache_path
        self._cache = load_cache(cache_path)

    def translate(self, text, target_lang='si', **kwargs):
        if not text or not text.strip():
            return ""

        key = get_cache_key(text, target_lang)

        if key in self._cache:
            logger.debug("Cache hit for text (len=%d)", len(text))
            return self._cache[key]

        result = self._translate_fn(text, target_lang=target_lang, **kwargs)
        self._cache[key] = result
        self._save()
        return result

    def _save(self):
        save_cache(self._cache, self._cache_path)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_cache.py -v
```
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add pdf_translator/cache.py tests/test_cache.py
git commit -m "feat: add disk-based translation cache"
```

---

### Task 5: Better Table Detection in `tables.py` (Agent D)

**Files:**
- Modify: `pdf_translator/tables.py`
- Create: `tests/test_tables.py`

**Improvements covered:** #10 (better table detection using `page.find_tables()`).

- [ ] **Step 1: Write tests**

Create `tests/test_tables.py`:

```python
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
        page.insert_text((72, 72), "Just a paragraph of text.")
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
        blocks = [{'type': 1, 'image': b'fake'}]
        self.assertEqual(identify_tables(blocks), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement `identify_tables_from_page` in `pdf_translator/tables.py`**

```python
import logging

logger = logging.getLogger(__name__)


def identify_tables_from_page(page):
    """Detect tables using PyMuPDF's built-in table finder.

    Args:
        page: A PyMuPDF page object.

    Returns:
        List of tables, each table is a list of rows, each row is a list of cell strings.
    """
    try:
        table_finder = page.find_tables()
        tables = []
        for table in table_finder.tables:
            table_data = table.extract()
            # Clean None cells and empty rows
            cleaned = []
            for row in table_data:
                cleaned_row = [cell if cell else "" for cell in row]
                if any(cell.strip() for cell in cleaned_row):
                    cleaned.append(cleaned_row)
            if cleaned:
                tables.append(cleaned)
        return tables
    except Exception as e:
        logger.warning("Table detection failed: %s. Falling back to heuristic.", e)
        return []


def identify_tables(blocks):
    """Fallback heuristic: identify table-like structures from PDF blocks.

    Type 0 = text block, Type 1 = image block.
    """
    tables = []
    for block in blocks:
        if block.get('type') == 0 and 'lines' in block:
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


def extract_tables_from_page(page, blocks):
    """Extract tables from a page — tries built-in detection first, falls back to heuristic.

    Called by extractor.py while the document is still open.
    Returns list of tables (each a list of rows of cell strings).
    """
    tables = identify_tables_from_page(page)
    if not tables:
        tables = identify_tables(blocks)
    return tables
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_tables.py -v
```
Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add pdf_translator/tables.py tests/test_tables.py
git commit -m "feat: add PyMuPDF built-in table detection with heuristic fallback"
```

---

### Task 6: PDF Output + Bilingual in `writer.py` (Agent E)

**Files:**
- Modify: `pdf_translator/writer.py`
- Create: `tests/test_writer.py`

**Improvements covered:** #3 (PDF output), #13 (bilingual output).

- [ ] **Step 1: Write tests**

Create `tests/test_writer.py`:

```python
import unittest
import os
from pdf_translator.writer import save_as_text, save_as_pdf


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
        save_as_text(self.output_path, self._make_pages(), ["Translated text"],
                     lambda x: x)
        self.assertTrue(os.path.exists(self.output_path))

    def test_contains_page_header(self):
        save_as_text(self.output_path, self._make_pages(), ["Translated text"],
                     lambda x: x)
        with open(self.output_path, 'r') as f:
            content = f.read()
        self.assertIn("--- Page 1 ---", content)
        self.assertIn("Translated text", content)

    def test_bilingual_includes_original(self):
        save_as_text(self.output_path, self._make_pages(), ["Translated text"],
                     lambda x: x, bilingual=True)
        with open(self.output_path, 'r') as f:
            content = f.read()
        self.assertIn("[Original]", content)
        self.assertIn("[Translated]", content)
        self.assertIn("Original text here", content)

    def test_non_bilingual_excludes_original(self):
        save_as_text(self.output_path, self._make_pages(), ["Translated text"],
                     lambda x: x, bilingual=False)
        with open(self.output_path, 'r') as f:
            content = f.read()
        self.assertNotIn("[Original]", content)
        self.assertNotIn("Original text here", content)


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
        # Verify it's a valid PDF
        with open(self.output_path, 'rb') as f:
            header = f.read(5)
        self.assertEqual(header, b'%PDF-')

    def test_pdf_has_content(self):
        save_as_pdf(self.output_path, self._make_pages(), ["Translated text"])
        self.assertTrue(os.path.getsize(self.output_path) > 100)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement full `writer.py`**

```python
import os
import logging

logger = logging.getLogger(__name__)

# fpdf2 is optional
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.debug("fpdf2 not installed — PDF output disabled")


def save_as_text(file_path, pages_content, translated_texts, translate_fn,
                 bilingual=False):
    """Save translated content to a text file.

    pages_content is a list of (text, blocks, table_data) tuples.
    table_data is pre-extracted by extractor.py while the doc was open.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for i, (original_text, blocks, table_data) in enumerate(pages_content):
            translated_text = translated_texts[i]

            f.write(f"--- Page {i + 1} ---\n")

            if bilingual:
                f.write("[Original]\n")
                f.write(original_text + "\n\n")
                f.write("[Translated]\n")

            f.write(translated_text + "\n\n")

            for table in table_data:
                for row in table:
                    translated_row = [translate_fn(cell) for cell in row]
                    f.write(" | ".join(translated_row) + "\n")
                f.write("\n")

            f.write("\n")

    logger.info("Saved text output: %s", file_path)


def save_as_pdf(file_path, pages_content, translated_texts):
    """Save translated content to a PDF file."""
    if not PDF_AVAILABLE:
        raise RuntimeError("fpdf2 is required for PDF output. Install with: pip install fpdf2")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Use a Unicode-compatible font
    # fpdf2 has built-in support for DejaVu
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    if os.path.exists(os.path.join(font_dir, 'DejaVuSans.ttf')):
        pdf.add_font('DejaVu', '', os.path.join(font_dir, 'DejaVuSans.ttf'), uni=True)
        font_name = 'DejaVu'
    else:
        # Fallback — use built-in font (limited Unicode support)
        font_name = 'Helvetica'
        logger.warning("DejaVuSans.ttf not found in %s — using Helvetica (limited Unicode)", font_dir)

    for i, (original_text, blocks, table_data) in enumerate(pages_content):
        translated_text = translated_texts[i]

        pdf.add_page()
        pdf.set_font(font_name, size=10)
        pdf.set_y(20)

        # Page header
        pdf.set_font(font_name, size=12)
        pdf.cell(0, 10, f"--- Page {i + 1} ---", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # Translated text
        pdf.set_font(font_name, size=10)
        for line in translated_text.split('\n'):
            pdf.multi_cell(0, 6, line)

    pdf.output(file_path)
    logger.info("Saved PDF output: %s", file_path)


def save_output(file_path, pages_content, translated_texts, translate_fn,
                output_format='txt', bilingual=False):
    """Save output in the requested format(s)."""
    base, _ = os.path.splitext(file_path)

    if output_format in ('txt', 'both'):
        txt_path = base + '.txt'
        save_as_text(txt_path, pages_content, translated_texts, translate_fn,
                     bilingual=bilingual)

    if output_format in ('pdf', 'both'):
        pdf_path = base + '.pdf'
        save_as_pdf(pdf_path, pages_content, translated_texts)
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_writer.py -v
```
Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add pdf_translator/writer.py tests/test_writer.py
git commit -m "feat: add PDF output and bilingual text output support"
```

---

## Phase 3: Wire Everything Together in main.py (Sequential)

### Task 7: Concurrency + Progress Bar + Batch Summary + Cache Integration

**Files:**
- Modify: `main.py`
- Modify: `pdf_translator/__init__.py`
- Update: `tests/test_integration.py`

**Improvements covered:** #5 (skip translated), #6 (concurrent translation), #11 (progress bar), #12 (config file), #14 (batch summary).

- [ ] **Step 1: Rewrite `main.py` with all features**

```python
import os
import sys
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from pdf_translator.cli import parse_args, setup_logging, merge_args_with_config
from pdf_translator.config import load_config
from pdf_translator.extractor import extract_pdf_content, parse_page_range
from pdf_translator.engines import translate_text
from pdf_translator.cache import CachedTranslator
from pdf_translator.writer import save_output

# tqdm is optional
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

logger = logging.getLogger(__name__)


def _translate_page(args):
    """Translate a single page — used by thread pool."""
    page_num, text, translate_fn = args
    return page_num, translate_fn(text)


def process_pdfs(settings):
    input_folder = settings['input_folder']
    output_folder = settings['output_folder']
    target_lang = settings['target_language']
    engine_name = settings.get('engine', 'google')
    api_key = settings.get('api_key')
    password = settings.get('password')
    force = settings.get('force', False)
    bilingual = settings.get('bilingual', False)
    output_format = settings.get('output_format', 'txt')
    max_workers = settings.get('max_workers', 3)
    page_range = parse_page_range(settings.get('pages'))

    if not os.path.exists(input_folder):
        logger.error("Input folder '%s' does not exist.", input_folder)
        sys.exit(1)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]

    if not pdf_files:
        logger.info("No PDF files found in '%s'.", input_folder)
        return

    # Set up cached translator
    def base_translate(text, target_lang=target_lang, **kw):
        return translate_text(
            text, target_lang=target_lang, engine_name=engine_name, api_key=api_key
        )

    cached = CachedTranslator(base_translate)
    translate_fn = lambda text: cached.translate(text, target_lang=target_lang)

    total_files = len(pdf_files)
    logger.info("Found %d PDF file(s) to process.", total_files)

    # Batch summary tracking
    start_time = time.time()
    results = {'success': 0, 'skipped': 0, 'failed': 0, 'total_pages': 0, 'errors': []}

    file_iter = tqdm(pdf_files, desc="Files", unit="file") if TQDM_AVAILABLE else pdf_files

    for file_idx, file_name in enumerate(file_iter, 1):

        pdf_path = os.path.join(input_folder, file_name)
        base_name = file_name.rsplit('.', 1)[0]
        output_file_path = os.path.join(output_folder, base_name + '.txt')

        # Skip already translated
        if not force and os.path.exists(output_file_path):
            input_mtime = os.path.getmtime(pdf_path)
            output_mtime = os.path.getmtime(output_file_path)
            if output_mtime > input_mtime:
                logger.info("Skipping (already translated): %s", file_name)
                results['skipped'] += 1
                continue

        if not TQDM_AVAILABLE:
            logger.info("[%d/%d] Processing: %s", file_idx, total_files, file_name)

        try:
            pages_content = extract_pdf_content(pdf_path, password=password,
                                                 page_range=page_range)
            num_pages = len(pages_content)
            results['total_pages'] += num_pages
            logger.info("  Extracted %d page(s)", num_pages)

            # Concurrent translation
            translated_texts = [None] * num_pages
            tasks = [(i, text, translate_fn) for i, (text, _b, _t) in enumerate(pages_content)]

            if max_workers > 1 and num_pages > 1:
                page_iter = tqdm(total=num_pages, desc="  Translating", unit="page", leave=False) if TQDM_AVAILABLE else None
                with ThreadPoolExecutor(max_workers=min(max_workers, num_pages)) as executor:
                    futures = {executor.submit(_translate_page, t): t[0] for t in tasks}
                    for future in as_completed(futures):
                        idx, result = future.result()
                        translated_texts[idx] = result
                        if page_iter:
                            page_iter.update(1)
                        else:
                            logger.info("  Translated page %d/%d", idx + 1, num_pages)
                if page_iter:
                    page_iter.close()
            else:
                for i, (text, _b, _t) in enumerate(pages_content):
                    if not TQDM_AVAILABLE:
                        logger.info("  Translating page %d/%d...", i + 1, num_pages)
                    translated_texts[i] = translate_fn(text)

            # Save output
            save_output(output_file_path, pages_content, translated_texts,
                        translate_fn, output_format=output_format, bilingual=bilingual)
            logger.info("  Saved: %s", output_file_path)
            results['success'] += 1

        except Exception as e:
            logger.error("  Error processing '%s': %s", file_name, e)
            results['failed'] += 1
            results['errors'].append((file_name, str(e)))
            continue

    # Batch summary
    elapsed = time.time() - start_time
    minutes, seconds = divmod(int(elapsed), 60)

    summary = (
        f"\n{'=' * 40}\n"
        f"  Batch Summary\n"
        f"{'=' * 40}\n"
        f"  Total files:    {total_files}\n"
        f"  Successful:     {results['success']}\n"
        f"  Skipped:        {results['skipped']}\n"
        f"  Failed:         {results['failed']}\n"
        f"  Total pages:    {results['total_pages']}\n"
        f"  Time elapsed:   {minutes}m {seconds}s\n"
    )

    if results['errors']:
        summary += "\n  Failed files:\n"
        for fname, err in results['errors']:
            summary += f"    - {fname}: {err}\n"

    summary += f"{'=' * 40}\n"
    logger.info(summary)


def main():
    args = parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, log_file=args.log)

    config_path = args.config
    if not config_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_config = os.path.join(base_dir, 'config.default.yaml')
        if os.path.exists(default_config):
            config_path = default_config

    config = load_config(config_path)
    settings = merge_args_with_config(args, config)

    process_pdfs(settings)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Update `pdf_translator/__init__.py`**

```python
from pdf_translator.engines import translate_text
from pdf_translator.extractor import extract_pdf_content
from pdf_translator.writer import save_as_text, save_as_pdf, save_output
from pdf_translator.tables import identify_tables, identify_tables_from_page, extract_tables_from_page
from pdf_translator.cache import CachedTranslator
```

- [ ] **Step 3: Update `tests/test_integration.py`**

```python
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

        # First run
        process_pdfs(settings)
        output_file = os.path.join(self.output_dir, 'test.txt')
        self.assertTrue(os.path.exists(output_file))
        first_mtime = os.path.getmtime(output_file)

        # Second run without force — should skip
        import time
        time.sleep(0.1)
        settings['force'] = False
        process_pdfs(settings)
        second_mtime = os.path.getmtime(output_file)
        self.assertEqual(first_mtime, second_mtime)  # File not modified


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run all tests**

```bash
pip install fpdf2 tqdm pyyaml pytesseract Pillow -q
python -m pytest tests/ -v
```
Expected: All PASS.

- [ ] **Step 5: Test the app end-to-end with CLI flags**

```bash
python main.py --help
python main.py --force --verbose
python main.py --lang si --format txt --bilingual --force
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: add concurrency, progress bar, batch summary, cache integration, and config support"
```

---

## Parallel Execution Strategy

```
┌──────────────────────────────────────────────────┐
│  Phase 1 — SEQUENTIAL (Task 1)                   │
│  Restructure codebase + CLI + Logging             │
│  Creates all module files as skeletons            │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│  Phase 2 — PARALLEL (5 agents, 0 conflicts)      │
│                                                   │
│  Agent A: Task 2 — OCR in extractor.py           │
│  Agent B: Task 3 — Multi-engine in engines.py    │
│  Agent C: Task 4 — Cache in cache.py             │
│  Agent D: Task 5 — Tables in tables.py           │
│  Agent E: Task 6 — PDF+bilingual in writer.py    │
│                                                   │
│  Each touches ONLY its own file + test file.     │
└──────────────────┬───────────────────────────────┘
                   │ all complete, merge branches
                   ▼
┌──────────────────────────────────────────────────┐
│  Phase 3 — SEQUENTIAL (Task 7)                   │
│  Wire everything in main.py + integration tests  │
│  Concurrency, progress, batch summary, config    │
└──────────────────────────────────────────────────┘
```

## Improvements Coverage Map

| # | Improvement | Task | Phase |
|---|-------------|------|-------|
| 1 | CLI arguments | Task 1 | 1 |
| 2 | OCR support | Task 2 | 2 |
| 3 | PDF output | Task 6 | 2 |
| 4 | Logging | Task 1 | 1 |
| 5 | Skip already translated | Task 7 | 3 |
| 6 | Concurrent translation | Task 7 | 3 |
| 7 | Translation cache | Task 4 | 2 |
| 8 | Multiple engines | Task 3 | 2 |
| 9 | Page range selection | Task 1 + 2 | 1 + 2 |
| 10 | Better table detection | Task 5 | 2 |
| 11 | Progress bar (tqdm) | Task 7 | 3 |
| 12 | Config file support | Task 1 + 7 | 1 + 3 |
| 13 | Bilingual output | Task 6 | 2 |
| 14 | Batch summary report | Task 7 | 3 |
| 15 | Password-protected PDFs | Task 2 | 2 |
