from deep_translator import GoogleTranslator
import logging
import time
import threading

logger = logging.getLogger("app.translation")

# Per-language rate limiting: skip translation if within this many seconds
# of the last translation for that language. Set to 5.0s to stay under
# Google's 5 req/s global limit.
_LANG_RATE_LIMIT = 8.0  # seconds per language

_LANG_LOCK = threading.Lock()
# {lang_name: last_translation_timestamp}
_lang_last_time = {}

# Global semaphore to serialize translation requests and avoid Google API rate limit
_translation_semaphore = threading.Semaphore(1)

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
        self._global_lock = threading.Lock()

    def translate(self, text, target_lang="en"):
        """Translate text synchronously. Returns the translated text
        or the original text if translation fails. Rate-limited per language."""
        if not text or not text.strip():
            return ""

        # Per-language rate limiting — atomically check and update under lock
        with _LANG_LOCK:
            last = _lang_last_time.get(target_lang, 0.0)
            if time.time() - last < _LANG_RATE_LIMIT:
                return None  # rate-limited

            # Mark as translating (prevents concurrent duplicates)
            _lang_last_time[target_lang] = time.time()

        try:
            lang_code = LANG_CODE_MAP.get(target_lang, target_lang)
            translator = GoogleTranslator(source="auto", target=lang_code)
            translated = translator.translate(text)
            # Update rate-limit timestamp only on success
            with _LANG_LOCK:
                _lang_last_time[target_lang] = time.time()
            return translated if translated else text
        except Exception as e:
            logger.error("Translation error (%s): %s", target_lang, e)
            return text

    def translate_async(self, text, target_lang, callback):
        """Non-blocking translation: runs in a background thread and calls
        callback(translated_text) when done. Skips if rate-limited.
        
        NOTE: Does NOT call self.translate() to avoid double rate-limit check.
        Instead, it does the translation directly since the rate limit slot
        is already reserved by this method.
        """
        if not text or not text.strip():
            return

        # Check per-language rate limit and reserve the slot.
        with _LANG_LOCK:
            last = _lang_last_time.get(target_lang, 0.0)
            if time.time() - last < _LANG_RATE_LIMIT:
                return  # language rate-limited, skip
            _lang_last_time[target_lang] = time.time()

        def _do_translate():
            # Serialize translation requests to avoid Google API rate limit
            _translation_semaphore.acquire()
            try:
                lang_code = LANG_CODE_MAP.get(target_lang, target_lang)
                translator = GoogleTranslator(source="auto", target=lang_code)
                translated = translator.translate(text)
                with _LANG_LOCK:
                    _lang_last_time[target_lang] = time.time()
                result = translated if translated else text
                callback(result)
            except Exception as e:
                logger.error("Async translation error (%s): %s", target_lang, e)
            finally:
                _translation_semaphore.release()

        t = threading.Thread(target=_do_translate, daemon=True)
        t.start()
