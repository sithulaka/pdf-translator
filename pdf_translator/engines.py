import time
import logging
from deep_translator import GoogleTranslator, MyMemoryTranslator

logger = logging.getLogger(__name__)

_translator_cache = {}
CHUNK_SIZE = 4500
MAX_RETRIES = 3
SUPPORTED_ENGINES = ['google', 'mymemory']


def create_engine(engine_name='google', target_lang='si', api_key=None):
    cache_key = f"{engine_name}:{target_lang}"
    if cache_key not in _translator_cache:
        if engine_name == 'google':
            _translator_cache[cache_key] = GoogleTranslator(source='auto', target=target_lang)
        elif engine_name == 'mymemory':
            _translator_cache[cache_key] = MyMemoryTranslator(source='auto', target=target_lang)
        else:
            raise ValueError(f"Unknown engine: '{engine_name}'. Available: {', '.join(SUPPORTED_ENGINES)}")
    return _translator_cache[cache_key]


def _translate_with_retry(translator, text):
    for attempt in range(MAX_RETRIES):
        try:
            result = translator.translate(text)
            return result if result else ""
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = (2 ** attempt) * 0.5
                logger.warning("Translation attempt %d failed: %s. Retrying in %.1fs...", attempt + 1, e, wait_time)
                time.sleep(wait_time)
            else:
                logger.error("Translation failed after %d attempts: %s. Using original text.", MAX_RETRIES, e)
                return text


def translate_text(text, target_lang='si', engine_name='google', api_key=None):
    if not text or not text.strip():
        return ""
    translator = create_engine(engine_name, target_lang, api_key)
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
