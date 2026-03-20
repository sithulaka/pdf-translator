import fitz  # PyMuPDF to handle PDF
import time
from deep_translator import GoogleTranslator

_translator_cache = {}
CHUNK_SIZE = 4500  # Under Google Translate's 5000 char limit
MAX_RETRIES = 3


def _get_translator(target_lang='si'):
    """Reuse translator instance per target language."""
    if target_lang not in _translator_cache:
        _translator_cache[target_lang] = GoogleTranslator(source='auto', target=target_lang)
    return _translator_cache[target_lang]


def _translate_with_retry(translator, text):
    """Translate with exponential backoff retry on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            result = translator.translate(text)
            return result if result else ""
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = (2 ** attempt) * 0.5
                print(f"  Translation attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  Translation failed after {MAX_RETRIES} attempts: {e}. Using original text.")
                return text


def translate_text(text, target_lang='si'):
    """Translate text with chunking for large texts and error handling."""
    if not text or not text.strip():
        return ""

    translator = _get_translator(target_lang)

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


def extract_pdf_content(pdf_path):
    """Extract text and blocks from each page of a PDF."""
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

    Type 0 = text block (has lines/spans), Type 1 = image block.
    Heuristic: text blocks with multiple lines where each line has
    multiple spans are likely table rows.
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


def save_translated_text_as_file(file_path, pages_content, translated_texts):
    """Save translated content and tables to a text file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        for i, (original_text, blocks) in enumerate(pages_content):
            translated_text = translated_texts[i]

            file.write(f"--- Page {i + 1} ---\n")
            file.write(translated_text + "\n")
            file.write("\n")

            tables = identify_tables(blocks)
            for table_data in tables:
                for row in table_data:
                    translated_row = [translate_text(cell) for cell in row]
                    file.write(" | ".join(translated_row) + "\n")
                file.write("\n")

            file.write("\n\n")
