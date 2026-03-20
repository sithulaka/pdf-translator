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

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

logger = logging.getLogger(__name__)


def _translate_page(args):
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

    def base_translate(text, target_lang=target_lang, **kw):
        return translate_text(text, target_lang=target_lang, engine_name=engine_name, api_key=api_key)

    cached = CachedTranslator(base_translate)
    translate_fn = lambda text: cached.translate(text, target_lang=target_lang)

    total_files = len(pdf_files)
    logger.info("Found %d PDF file(s) to process.", total_files)

    start_time = time.time()
    results = {'success': 0, 'skipped': 0, 'failed': 0, 'total_pages': 0, 'errors': []}

    file_iter = tqdm(pdf_files, desc="Files", unit="file") if TQDM_AVAILABLE else pdf_files

    for file_idx, file_name in enumerate(file_iter, 1):
        pdf_path = os.path.join(input_folder, file_name)
        base_name = file_name.rsplit('.', 1)[0]
        output_file_path = os.path.join(output_folder, base_name + '.txt')

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
            pages_content = extract_pdf_content(pdf_path, password=password, page_range=page_range)
            num_pages = len(pages_content)
            results['total_pages'] += num_pages
            logger.info("  Extracted %d page(s)", num_pages)

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

            save_output(output_file_path, pages_content, translated_texts,
                        translate_fn, output_format=output_format, bilingual=bilingual)
            logger.info("  Saved: %s", output_file_path)
            results['success'] += 1

        except Exception as e:
            logger.error("  Error processing '%s': %s", file_name, e)
            results['failed'] += 1
            results['errors'].append((file_name, str(e)))
            continue

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
