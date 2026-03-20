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
    logger.info("Found %d PDF file(s) to process.", total_files)

    for file_idx, file_name in enumerate(pdf_files, 1):
        pdf_path = os.path.join(input_folder, file_name)
        output_file_path = os.path.join(output_folder, file_name.rsplit('.', 1)[0] + '.txt')

        if not force and os.path.exists(output_file_path):
            input_mtime = os.path.getmtime(pdf_path)
            output_mtime = os.path.getmtime(output_file_path)
            if output_mtime > input_mtime:
                logger.info("[%d/%d] Skipping (already translated): %s", file_idx, total_files, file_name)
                continue

        logger.info("[%d/%d] Processing: %s", file_idx, total_files, file_name)

        try:
            pages_content = extract_pdf_content(pdf_path, password=password, page_range=page_range)
            logger.info("  Extracted %d page(s)", len(pages_content))

            translated_texts = []
            for page_num, (text, _blocks, _tables) in enumerate(pages_content, 1):
                logger.info("  Translating page %d/%d...", page_num, len(pages_content))
                translated_texts.append(translate_text(text, target_lang=target_lang, engine_name=engine_name, api_key=api_key))

            translate_fn = lambda cell: translate_text(cell, target_lang=target_lang, engine_name=engine_name, api_key=api_key)
            save_as_text(output_file_path, pages_content, translated_texts, translate_fn, bilingual=bilingual)
            logger.info("  Saved: %s", output_file_path)

        except Exception as e:
            logger.error("  Error processing '%s': %s", file_name, e)
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
