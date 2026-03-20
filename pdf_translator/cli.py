import argparse
import logging
import os


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='PDF Translator — Extract text from PDFs and translate to any language.'
    )
    parser.add_argument('--input', '-i', default=None, help='Input folder (default: input_pdfs)')
    parser.add_argument('--output', '-o', default=None, help='Output folder (default: output_texts)')
    parser.add_argument('--lang', '-l', default=None, help='Target language code (default: si)')
    parser.add_argument('--format', '-f', choices=['txt', 'pdf', 'both'], default=None, help='Output format (default: txt)')
    parser.add_argument('--engine', '-e', choices=['google', 'mymemory'], default=None, help='Translation engine (default: google)')
    parser.add_argument('--api-key', default=None, help='API key for translation engines')
    parser.add_argument('--pages', default=None, help='Page range, e.g. "1-5" or "3,7,10-15"')
    parser.add_argument('--password', default=None, help='Password for encrypted PDFs')
    parser.add_argument('--bilingual', action='store_true', default=None, help='Include original text alongside translation')
    parser.add_argument('--force', action='store_true', default=False, help='Re-translate even if output exists')
    parser.add_argument('--workers', type=int, default=None, help='Concurrent translation workers (default: 3)')
    parser.add_argument('--config', default=None, help='Path to config YAML file')
    parser.add_argument('--verbose', '-v', action='store_true', default=False, help='Debug logging')
    parser.add_argument('--quiet', '-q', action='store_true', default=False, help='Warnings only')
    parser.add_argument('--log', default=None, help='Write logs to file')
    return parser.parse_args(argv)


def setup_logging(verbose=False, quiet=False, log_file=None):
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.WARNING
    else:
        level = logging.INFO
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                        datefmt='%H:%M:%S', handlers=handlers)


def merge_args_with_config(args, config):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    settings = dict(config)
    if args.input is not None: settings['input_folder'] = args.input
    if args.output is not None: settings['output_folder'] = args.output
    if args.lang is not None: settings['target_language'] = args.lang
    if args.format is not None: settings['output_format'] = args.format
    if args.engine is not None: settings['engine'] = args.engine
    if args.api_key is not None: settings['api_key'] = args.api_key
    if args.pages is not None: settings['pages'] = args.pages
    if args.password is not None: settings['password'] = args.password
    if args.bilingual is not None: settings['bilingual'] = args.bilingual
    if args.workers is not None: settings['max_workers'] = args.workers
    settings['force'] = args.force
    for key in ('input_folder', 'output_folder'):
        if not os.path.isabs(settings[key]):
            settings[key] = os.path.join(base_dir, settings[key])
    return settings
