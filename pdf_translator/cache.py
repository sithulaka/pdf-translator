import hashlib
import json
import os
import logging

logger = logging.getLogger(__name__)

CACHE_FILE = '.translation_cache.json'


def _get_cache_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', CACHE_FILE)


def load_cache():
    path = _get_cache_path()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    path = _get_cache_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_cache_key(text, target_lang):
    return hashlib.md5(f"{target_lang}:{text}".encode()).hexdigest()
