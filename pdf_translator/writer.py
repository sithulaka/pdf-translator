import os
import logging

logger = logging.getLogger(__name__)

try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.debug("fpdf2 not installed — PDF output disabled")


def save_as_text(file_path, pages_content, translated_texts, translate_fn, bilingual=False):
    """Save translated content to a text file.
    pages_content is a list of (text, blocks, table_data) tuples.
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
    """Save translated content to a PDF file using fpdf2."""
    if not PDF_AVAILABLE:
        raise RuntimeError("fpdf2 is required for PDF output. Install with: pip install fpdf2")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    font_name = 'Helvetica'

    for i, (original_text, blocks, table_data) in enumerate(pages_content):
        translated_text = translated_texts[i]
        pdf.add_page()
        pdf.set_font(font_name, size=12)
        pdf.cell(0, 10, f"--- Page {i + 1} ---", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        pdf.set_font(font_name, size=10)
        for line in translated_text.split('\n'):
            # fpdf2 multi_cell handles long lines
            pdf.multi_cell(0, 6, line.encode('latin-1', 'replace').decode('latin-1'))

    pdf.output(file_path)
    logger.info("Saved PDF output: %s", file_path)


def save_output(file_path, pages_content, translated_texts, translate_fn,
                output_format='txt', bilingual=False):
    """Save output in the requested format(s)."""
    base, _ = os.path.splitext(file_path)

    if output_format in ('txt', 'both'):
        txt_path = base + '.txt'
        save_as_text(txt_path, pages_content, translated_texts, translate_fn, bilingual=bilingual)

    if output_format in ('pdf', 'both'):
        pdf_path = base + '.pdf'
        save_as_pdf(pdf_path, pages_content, translated_texts)
