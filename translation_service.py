from deep_translator import GoogleTranslator
import logging
import time
import threading

logger = logging.getLogger(__name__)

_translation_lock = threading.Lock()
_MIN_TRANSLATION_INTERVAL = 10000

LANG_CODE_MAP = {
    "English": "en",
    "French": "fr",
    "Spanish": "es",
    "Arabic": "ar",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
}


class TranslationService:
    def __init__(self):
        # We create a fresh translator per call to avoid rate limits
        # and threading issues with shared state
        self._last_translation_time = 0.0
        pass

    def translate(self, text, target_lang="en"):
        if not text or not text.strip():
            return ""
        # Rate limit to avoid Google API throttling
        with _translation_lock:
            now = time.time()
            elapsed = now - self._last_translation_time
            if elapsed < _MIN_TRANSLATION_INTERVAL:
                time.sleep(_MIN_TRANSLATION_INTERVAL - elapsed)
            self._last_translation_time = time.time()
        try:
            lang_code = LANG_CODE_MAP.get(target_lang, target_lang)
            translator = GoogleTranslator(source="auto", target=lang_code)
            translated = translator.translate(text)
            return translated if translated else text
        except Exception as e:
            logger.error("Translation error: %s", e)
            return text
