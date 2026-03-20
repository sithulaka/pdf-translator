# PDF Translator

## Overview

PDF Translator is a Python tool that extracts text from PDF documents, translates it into Sinhala using Google Translate, and saves the translated content as structured text files. It handles large documents by chunking text, retries failed translations automatically, and detects tables within PDFs.

## How It Works

```
input_pdfs/              main.py                    pdf_translator/translator.py           output_texts/
+-----------+     +------------------+     +-------------------------------+     +-------------+
| your.pdf  | --> | Finds all PDFs   | --> | 1. extract_pdf_content()      | --> | your.txt    |
| files     |     | in input folder  |     |    Opens PDF with PyMuPDF     |     | translated  |
+-----------+     | and processes    |     |    Extracts text per page     |     | text files  |
                  | them one by one  |     |    Extracts layout blocks     |     +-------------+
                  +------------------+     |                               |
                                           | 2. translate_text()           |
                                           |    Chunks text (< 4500 chars) |
                                           |    Translates via Google API  |
                                           |    Retries on failure (3x)    |
                                           |    Rate limits between chunks |
                                           |                               |
                                           | 3. identify_tables()          |
                                           |    Finds table-like blocks    |
                                           |    Translates table cells     |
                                           |                               |
                                           | 4. save_translated_text_as_file() |
                                           |    Writes page-by-page output |
                                           |    Includes translated tables |
                                           +-------------------------------+
```

### Step-by-step flow

1. `main.py` scans `input_pdfs/` for all `.pdf` files
2. For each PDF, `extract_pdf_content()` opens it with PyMuPDF and extracts text + layout blocks from every page
3. Each page's text is passed to `translate_text()`, which:
   - Skips empty pages
   - Splits text into chunks under 4500 characters (Google Translate limit is 5000)
   - Translates each chunk with automatic retry (up to 3 attempts with exponential backoff)
   - Adds a 0.5s delay between chunks to avoid rate limiting
4. `identify_tables()` detects table-like structures using a heuristic (text blocks with multiple lines containing multiple spans)
5. Table cell content is also translated
6. Everything is written to a `.txt` file in `output_texts/` with page markers (`--- Page 1 ---`)

### Output format

```
--- Page 1 ---
<translated text>

<translated table row 1 cell1 | cell2 | cell3>
<translated table row 2 cell1 | cell2 | cell3>


--- Page 2 ---
<translated text>

```

## Features

- **Text Extraction** - Extracts text from PDF files using PyMuPDF
- **Translation** - Translates to Sinhala via Google Translate (auto-detects source language)
- **Text Chunking** - Handles large pages by splitting into chunks under 4500 characters
- **Retry with Backoff** - Retries failed translations up to 3 times with exponential backoff
- **Rate Limiting** - 0.5s delay between translation chunks to prevent API throttling
- **Table Detection** - Identifies and translates table content from PDFs
- **Error Handling** - Skips problematic files and continues processing the rest
- **Progress Output** - Shows file count, page-by-page translation progress

## Installation

### Clone the Repository

```bash
git clone https://github.com/sithulaka/pdf-translator.git
cd pdf-translator
```

### Set Up a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pymupdf` | 1.23.6 | PDF text and layout extraction |
| `deep-translator` | 1.7.0 | Google Translate API wrapper |

## Usage

1. Place your PDF files in the `input_pdfs/` folder

2. Run the translator:

   ```bash
   python main.py
   ```

3. Check the translated output in `output_texts/`

### Example output

```
$ python main.py
Found 2 PDF file(s) to process.

[1/2] Processing: report.pdf
  Extracted 3 page(s)
  Translating page 1/3...
  Translating page 2/3...
  Translating page 3/3...
  Saved: /path/to/output_texts/report.txt

[2/2] Processing: article.pdf
  Extracted 1 page(s)
  Translating page 1/1...
  Saved: /path/to/output_texts/article.txt

Done.
```

## Folder Structure

```
pdf-translator/
├── pdf_translator/
│   ├── __init__.py          # Package init
│   └── translator.py        # Core logic (extract, translate, save)
├── tests/
│   ├── __init__.py
│   ├── test_translator.py   # Unit tests for translate_text()
│   └── test_integration.py  # End-to-end pipeline tests
├── input_pdfs/              # Place your PDFs here
├── output_texts/            # Translated .txt files appear here
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── LICENSE                  # MIT License
└── README.md
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Limitations

- **Scanned PDFs** - Only works with text-based PDFs. Scanned/image-only PDFs produce no output (requires OCR)
- **Formatting** - Output is plain text. Original PDF formatting (fonts, bold, columns) is not preserved
- **Target Language** - Currently hardcoded to Sinhala (`si`). Change the `target_lang` parameter in code to translate to other languages
- **Tables** - Table detection uses heuristics and may not catch all table formats

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Fork the repository and submit a pull request with your improvements or bug fixes.

## Connect with me

<p align="left">
<a href="https://linkedin.com/in/sithulaka" target="blank"><img align="center" src="https://github.com/sithulaka/sithulaka/blob/main/image/icon/linked-in-alt.svg" alt="sithulaka" height="30" width="40" /></a>
<a href="https://twitter.com/sithulaka" target="blank"><img align="center" src="https://github.com/sithulaka/sithulaka/blob/main/image/icon/twitter.svg" alt="sithulaka" height="30" width="40" /></a>
<a href="https://fb.com/senithu.sithulaka.7" target="blank"><img align="center" src="https://github.com/sithulaka/sithulaka/blob/main/image/icon/facebook.svg" alt="sithulaka" height="30" width="40" /></a>
<a href="https://instagram.com/_sithulaka_" target="blank"><img align="center" src="https://github.com/sithulaka/sithulaka/blob/main/image/icon/instagram.svg" alt="sithulaka" height="30" width="40" /></a>
</p>
