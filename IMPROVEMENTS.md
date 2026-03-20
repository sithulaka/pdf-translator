# PDF Translator - Improvements Roadmap

## High Priority

### 1. CLI Arguments — Make the app configurable without editing code

**Current:** Target language (Sinhala), input/output folders are all hardcoded.

**Improvement:** Add `argparse` CLI support.

```bash
# Current — no options
python main.py

# Improved
python main.py --input docs/ --output translated/ --lang ta
python main.py --lang en        # translate to English
python main.py --help           # show usage
```

**Why:** Users currently have to edit `main.py` and `translator.py` source code to change the language or folders. This should be a runtime option.

**Files:** `main.py`

---

### 2. OCR Support — Handle scanned/image-based PDFs

**Current:** Only works with text-based PDFs. Scanned documents produce empty output because `page.get_text()` returns nothing for image pages.

**Improvement:** Integrate `pytesseract` + `Pillow` for OCR fallback. When a page has no extractable text but contains images, run OCR on the page image.

```python
# Detect image-only pages and OCR them
text = page.get_text("text")
if not text.strip():
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img)
```

**Why:** Many real-world PDFs are scanned documents. Without OCR, the app is useless for a large portion of PDFs.

**Files:** `pdf_translator/translator.py`, `requirements.txt`
**New deps:** `pytesseract`, `Pillow`

---

### 3. Translated PDF Output — Preserve document format

**Current:** Output is plain `.txt` files. All formatting, layout, fonts, and structure are lost.

**Improvement:** Add option to output translated PDFs using `reportlab` or `fpdf2`. Recreate the PDF with translated text placed at the same positions as the original.

```bash
python main.py --format pdf    # output as translated PDF
python main.py --format txt    # output as text (default)
python main.py --format both   # output both formats
```

**Why:** Users often need the translated document in a presentable format, not raw text. This is the most requested feature for any document translator.

**Files:** New `pdf_translator/pdf_writer.py`, `main.py`, `requirements.txt`
**New deps:** `fpdf2` or `reportlab`

---

### 4. Logging — Replace print statements with proper logging

**Current:** All output uses `print()`. No way to control verbosity, write to log files, or suppress output.

**Improvement:** Use Python's `logging` module with configurable levels.

```python
import logging
logger = logging.getLogger(__name__)

# In translate_text:
logger.warning("Translation attempt %d failed: %s", attempt + 1, e)

# In main.py:
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
```

```bash
python main.py --verbose       # DEBUG level
python main.py --quiet         # WARNING level only
python main.py --log out.log   # write to file
```

**Why:** `print()` statements can't be filtered, timestamped, or redirected properly. Logging is essential for debugging production issues and batch processing.

**Files:** `pdf_translator/translator.py`, `main.py`

---

### 5. Skip Already Translated Files

**Current:** Every run re-translates all PDFs, even if the output already exists and the source hasn't changed.

**Improvement:** Check if output file exists and is newer than the input PDF. Skip translation if already done.

```python
if os.path.exists(output_file_path):
    input_mtime = os.path.getmtime(pdf_path)
    output_mtime = os.path.getmtime(output_file_path)
    if output_mtime > input_mtime:
        print(f"  Skipping (already translated): {file_name}")
        continue
```

```bash
python main.py                 # skip already translated
python main.py --force         # re-translate everything
```

**Why:** Translating is slow (API calls with rate limiting). Re-translating unchanged files wastes time and API quota.

**Files:** `main.py`

---

## Medium Priority

### 6. Concurrent Translation — Process multiple pages in parallel

**Current:** Pages are translated sequentially, one at a time. A 50-page PDF translates 50 times slower than needed.

**Improvement:** Use `concurrent.futures.ThreadPoolExecutor` to translate multiple pages concurrently (respecting rate limits).

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(translate_text, text): i for i, (text, _) in enumerate(pages_content)}
    for future in as_completed(futures):
        idx = futures[future]
        translated_texts[idx] = future.result()
```

**Why:** Translation is I/O-bound (network requests). Concurrency can reduce total time by 3-5x without hitting rate limits.

**Files:** `main.py` or `pdf_translator/translator.py`

---

### 7. Translation Cache — Don't re-translate identical text

**Current:** Every translation call hits the Google Translate API, even for identical text (e.g., headers, footers, repeated content across pages).

**Improvement:** Add a simple disk-based cache using `hashlib` + JSON.

```python
import hashlib, json

CACHE_FILE = "translation_cache.json"

def _get_cache_key(text, target_lang):
    return hashlib.md5(f"{target_lang}:{text}".encode()).hexdigest()

def translate_text_cached(text, target_lang='si'):
    key = _get_cache_key(text, target_lang)
    cache = _load_cache()
    if key in cache:
        return cache[key]
    result = translate_text(text, target_lang)
    cache[key] = result
    _save_cache(cache)
    return result
```

**Why:** PDFs often have repeated headers, footers, and boilerplate text. Caching avoids redundant API calls and speeds up re-runs.

**Files:** `pdf_translator/translator.py`

---

### 8. Multiple Translation Backends

**Current:** Only supports Google Translate via `deep-translator`. If Google rate-limits or blocks, there's no fallback.

**Improvement:** Support multiple translation engines (Google, MyMemory, LibreTranslate, DeepL) with automatic fallback.

```bash
python main.py --engine google     # default
python main.py --engine deepl --api-key YOUR_KEY
python main.py --engine libre --url http://localhost:5000
```

```python
ENGINES = {
    'google': lambda: GoogleTranslator(source='auto', target=target_lang),
    'mymemory': lambda: MyMemoryTranslator(source='auto', target=target_lang),
    'deepl': lambda: DeeplTranslator(api_key=key, target=target_lang),
}
```

**Why:** Google's free tier has rate limits. Users with DeepL API keys get better quality. Self-hosted LibreTranslate gives privacy. Having options makes the tool more broadly useful.

**Files:** `pdf_translator/translator.py`, `main.py`

---

### 9. Page Range Selection

**Current:** Translates all pages in every PDF. No way to translate only specific pages.

**Improvement:** Add `--pages` flag to select a range.

```bash
python main.py --pages 1-5         # first 5 pages only
python main.py --pages 3,7,10-15   # specific pages
```

**Why:** Large PDFs (100+ pages) take a long time. Users often only need specific sections translated.

**Files:** `main.py`, `pdf_translator/translator.py`

---

### 10. Better Table Detection — Use PyMuPDF's built-in table finder

**Current:** Table detection uses a heuristic (multi-span text blocks). This misses many real tables and can false-positive on multi-column text.

**Improvement:** PyMuPDF 1.23.x has `page.find_tables()` which uses actual table structure detection.

```python
def identify_tables(page):
    tables = page.find_tables()
    results = []
    for table in tables:
        table_data = table.extract()  # returns list of rows
        results.append(table_data)
    return results
```

**Why:** The heuristic approach is unreliable. The built-in method uses line detection and cell boundary analysis, producing far more accurate results.

**Files:** `pdf_translator/translator.py`

---

## Low Priority

### 11. Progress Bar — Visual feedback with `tqdm`

**Current:** Progress is shown as text lines (`Translating page 2/10...`).

**Improvement:** Use `tqdm` for a visual progress bar.

```
Processing: report.pdf
Extracting pages: 100%|████████████████| 10/10
Translating:       60%|██████████░░░░░░|  6/10  [00:12<00:08]
```

**Why:** Better UX, especially for large documents. Shows estimated time remaining.

**Files:** `main.py`
**New deps:** `tqdm`

---

### 12. Config File Support

**Current:** All settings require CLI flags or code changes.

**Improvement:** Support a `config.yaml` or `config.json` for default settings.

```yaml
# config.yaml
target_language: si
input_folder: input_pdfs
output_folder: output_texts
output_format: txt
engine: google
max_workers: 3
```

```bash
python main.py                          # uses config.yaml defaults
python main.py --lang ta                # override language
python main.py --config custom.yaml     # use different config
```

**Why:** Users who repeatedly run the app with the same settings shouldn't need to pass flags every time.

**Files:** `main.py`, new `config.yaml`
**New deps:** `pyyaml`

---

### 13. Bilingual Output — Side-by-side original and translated text

**Current:** Only translated text is saved. Original text is discarded.

**Improvement:** Add option to include original text alongside translation.

```
--- Page 1 ---
[Original]
Hello World. This is a test document.

[Translated - Sinhala]
හෙලෝ වර්ල්ඩ්. මෙය පරිවර්තනය සඳහා පරීක්ෂණ ලේඛනයකි.
```

```bash
python main.py --bilingual     # include original + translated
```

**Why:** Useful for review, proofreading, and language learning. Lets users verify translation quality.

**Files:** `pdf_translator/translator.py`

---

### 14. Batch Summary Report

**Current:** Success/failure per file is printed to console and lost after the session.

**Improvement:** Generate a summary report after batch processing.

```
=== Batch Summary ===
Total files:      10
Successful:        8
Failed:            2
Total pages:      47
Time elapsed:   2m 34s

Failed files:
  - corrupted.pdf: Cannot open damaged document
  - locked.pdf: Document is password protected
```

**Why:** When processing dozens of files, users need a clear summary of what worked and what didn't, without scrolling through console output.

**Files:** `main.py`

---

### 15. Password-Protected PDF Support

**Current:** Password-protected PDFs crash with an unhandled error.

**Improvement:** Accept a password flag or prompt for it.

```bash
python main.py --password secret123
```

```python
doc = fitz.open(pdf_path)
if doc.is_encrypted:
    if not doc.authenticate(password):
        raise ValueError("Wrong password")
```

**Why:** Many corporate and legal documents are password-protected. Supporting them expands the tool's usefulness.

**Files:** `pdf_translator/translator.py`, `main.py`

---

## Summary

| # | Improvement | Priority | Effort | Impact |
|---|-------------|----------|--------|--------|
| 1 | CLI arguments | High | Low | High |
| 2 | OCR support | High | Medium | High |
| 3 | Translated PDF output | High | High | High |
| 4 | Proper logging | High | Low | Medium |
| 5 | Skip already translated | High | Low | Medium |
| 6 | Concurrent translation | Medium | Medium | High |
| 7 | Translation cache | Medium | Low | Medium |
| 8 | Multiple translation engines | Medium | Medium | Medium |
| 9 | Page range selection | Medium | Low | Medium |
| 10 | Better table detection | Medium | Low | Medium |
| 11 | Progress bar (tqdm) | Low | Low | Low |
| 12 | Config file support | Low | Low | Low |
| 13 | Bilingual output | Low | Low | Low |
| 14 | Batch summary report | Low | Low | Low |
| 15 | Password-protected PDFs | Low | Low | Low |

## Recommended Implementation Order

Start with the quick wins that make the app immediately more useful:

1. **CLI arguments (#1)** — Foundation for all other features, low effort
2. **Skip already translated (#5)** — Saves time on every run
3. **Proper logging (#4)** — Makes debugging easier for everything after
4. **Better table detection (#10)** — One function swap, big accuracy gain
5. **OCR support (#2)** — Unlocks scanned PDFs
6. **Translation cache (#7)** — Speeds up repeated runs
7. **Page range selection (#9)** — Quick to add, useful for large PDFs
8. **Concurrent translation (#6)** — Significant speed boost
9. **Translated PDF output (#3)** — Highest effort but most impactful feature
10. Everything else as needed
