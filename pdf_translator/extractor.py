import fitz
import logging

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

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
