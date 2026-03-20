import fitz
import logging

logger = logging.getLogger(__name__)


def extract_pdf_content(pdf_path, password=None, page_range=None):
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
            table_data = extract_tables_from_page(page, blocks)
            pages.append((text, blocks, table_data))
    finally:
        doc.close()
    logger.debug("Extracted %d page(s) from %s", len(pages), pdf_path)
    return pages


def parse_page_range(page_str):
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
