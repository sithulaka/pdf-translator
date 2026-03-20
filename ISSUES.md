# PDF Translator - Issues Report

## Critical Issues (App-Breaking)

### 1. `__init__.py` is misnamed as `inite.py`

- **File:** `pdf_translator/inite.py`
- **Problem:** The Python package init file is named `inite.py` instead of `__init__.py`. While the app may still work if Python treats the directory as a namespace package (Python 3.3+), this is incorrect and can cause import failures depending on the Python version and environment configuration.
- **Fix:** Rename `pdf_translator/inite.py` to `pdf_translator/__init__.py`.

### 2. Google Translate 5000 character limit will crash on large pages

- **File:** `pdf_translator/translator.py:4-6`
- **Problem:** `GoogleTranslator.translate()` from `deep-translator` has a **5000 character limit** per request. If any PDF page has more than 5000 characters of text, the translation call will raise a `NotValidLength` exception and crash the entire process. There is no text chunking or error handling.
- **Fix:** Split text into chunks of ≤5000 characters before translating, then join the results.

### 3. No error handling anywhere

- **File:** `main.py`, `pdf_translator/translator.py`
- **Problem:** There are zero `try/except` blocks in the entire application. Any of the following will cause an unhandled crash:
  - Network failure during translation (no internet)
  - Corrupt or password-protected PDF
  - Google Translate rate limiting or API errors
  - Empty PDF pages returning `None` from translation
  - Missing input folder
- **Fix:** Add error handling around PDF extraction, translation calls, and file I/O operations.

---

## Major Issues (Incorrect Behavior)

### 4. `identify_tables()` logic is wrong — `type == 1` means images, not tables

- **File:** `pdf_translator/translator.py:20-30`
- **Problem:** In PyMuPDF's block dictionary, `type == 0` means text blocks and `type == 1` means **image blocks**, not table blocks. The function checks for `type == 1` and then tries to access `lines` and `spans` — but image blocks don't have `lines` or `spans` keys. This means:
  - Tables are never detected (they are type 0 text blocks)
  - If an image block somehow had a `lines` key, it would produce garbage
- **Fix:** Use a proper table extraction approach. PyMuPDF 1.23.x has `page.find_tables()` for actual table detection, or use heuristics on text block positions.

### 5. `translate_text()` can return `None` for empty text

- **File:** `pdf_translator/translator.py:4-6`
- **Problem:** If a PDF page has no extractable text (e.g., scanned image-only pages), the text will be an empty string. `GoogleTranslator.translate("")` may return `None`. This `None` is then written to the file on line 39 with `translated_text + "\n"`, which will raise a `TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'`.
- **Fix:** Check for empty/None text before translating and handle gracefully.

### 6. Tables are not translated

- **File:** `pdf_translator/translator.py:42-47`
- **Problem:** Even if table detection worked correctly, the table content is written to the output file **without being translated**. Only the page text is translated, but tables are written as-is in the original language.
- **Fix:** Pass table cell text through `translate_text()` before writing.

### 7. PDF document is never closed

- **File:** `pdf_translator/translator.py:8-18`
- **Problem:** `fitz.open(pdf_path)` opens the PDF but `doc.close()` is never called. This leaks file handles and can cause issues when processing many PDFs. Should use a `with` statement or explicitly close the document.
- **Fix:** Use `with fitz.open(pdf_path) as doc:` or call `doc.close()` in a `finally` block.

---

## Minor Issues (Quality / Robustness)

### 8. Relative paths break when script is run from a different directory

- **File:** `main.py:25-26`
- **Problem:** `input_folder = 'input_pdfs'` and `output_folder = 'output_texts'` are relative paths. If the script is run from any directory other than the project root (e.g., `python /path/to/pdf-translator/main.py`), it will look for `input_pdfs/` relative to the current working directory, not the project directory.
- **Fix:** Use `os.path.dirname(os.path.abspath(__file__))` to resolve paths relative to the script location.

### 9. No input folder existence check

- **File:** `main.py:8`
- **Problem:** If the `input_pdfs/` folder doesn't exist, `os.listdir(input_folder)` will raise a `FileNotFoundError`. The output folder is created if missing, but the input folder is not checked.
- **Fix:** Check if the input folder exists and provide a clear error message.

### 10. `reportlab` is an unused dependency

- **File:** `requirements.txt:3`
- **Problem:** `reportlab==3.6.12` is listed in requirements but is never imported or used anywhere in the code. This adds unnecessary install time and potential dependency conflicts.
- **Fix:** Remove `reportlab` from `requirements.txt`.

### 11. No progress feedback for large batches

- **File:** `main.py:8-22`
- **Problem:** The only output is a print statement after each file is fully processed. For large PDFs with many pages, there is no indication that the app is working — it appears to hang. No per-page progress, no file count (e.g., "Processing 3/10...").
- **Fix:** Add progress logging per page and per file.

### 12. Google Translate rate limiting with no backoff

- **File:** `pdf_translator/translator.py:4-6`
- **Problem:** Each page triggers a separate Google Translate API call with no delay. Processing many PDFs or PDFs with many pages can trigger Google's rate limiting, causing `TooManyRequests` exceptions with no retry logic.
- **Fix:** Add rate limiting (e.g., `time.sleep()` between calls) and retry logic with exponential backoff.

### 13. A new `GoogleTranslator` instance is created per call

- **File:** `pdf_translator/translator.py:5`
- **Problem:** Every call to `translate_text()` creates a new `GoogleTranslator` object. This is wasteful and adds overhead, especially when translating many pages.
- **Fix:** Create the translator instance once and reuse it.

---

## Summary

| # | Issue | Severity | File |
|---|-------|----------|------|
| 1 | `__init__.py` misnamed as `inite.py` | Critical | `pdf_translator/inite.py` |
| 2 | No text chunking (5000 char limit) | Critical | `translator.py:4-6` |
| 3 | No error handling anywhere | Critical | All files |
| 4 | Table detection logic is wrong (`type==1` = images) | Major | `translator.py:20-30` |
| 5 | `translate_text()` can return `None` | Major | `translator.py:4-6` |
| 6 | Tables are not translated | Major | `translator.py:42-47` |
| 7 | PDF document never closed (file handle leak) | Major | `translator.py:8-18` |
| 8 | Relative paths break from other directories | Minor | `main.py:25-26` |
| 9 | No input folder existence check | Minor | `main.py:8` |
| 10 | `reportlab` is unused dependency | Minor | `requirements.txt` |
| 11 | No progress feedback | Minor | `main.py:8-22` |
| 12 | No rate limiting / retry for Google Translate | Minor | `translator.py:4-6` |
| 13 | New translator instance created per call | Minor | `translator.py:5` |
