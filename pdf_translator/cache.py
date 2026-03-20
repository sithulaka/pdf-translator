import hashlib
import json
import os
import logging

logger = logging.getLogger(__name__)

CACHE_FILE = '.translation_cache.json'


def _default_cache_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', CACHE_FILE)


def load_cache(path=None):
    path = path or _default_cache_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to load cache: %s", e)
    return {}


def save_cache(cache, path=None):
    path = path or _default_cache_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.warning("Failed to save cache: %s", e)


def get_cache_key(text, target_lang):
    return hashlib.md5(f"{target_lang}:{text}".encode()).hexdigest()


class CachedTranslator:
    def __init__(self, translate_fn, cache_path=None):
        self._translate_fn = translate_fn
        self._cache_path = cache_path
        self._cache = load_cache(cache_path)

    def translate(self, text, target_lang='si', **kwargs):
        if not text or not text.strip():
            return ""
        key = get_cache_key(text, target_lang)
        if key in self._cache:
            logger.debug("Cache hit for text (len=%d)", len(text))
            return self._cache[key]
        result = self._translate_fn(text, target_lang=target_lang, **kwargs)
        self._cache[key] = result
        self._save()
        return result

    def _save(self):
        save_cache(self._cache, self._cache_path)
