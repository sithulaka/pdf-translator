import logging

logger = logging.getLogger(__name__)


def save_as_text(file_path, pages_content, translated_texts, translate_fn, bilingual=False):
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
