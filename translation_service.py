from deep_translator import GoogleTranslator
import logging
import time
import threading

logger = logging.getLogger(__name__)

# Per-language rate limiting: skip translation if within this many seconds
# of the last translation for that language.
_LANG_RATE_LIMIT = 3.0  # seconds

_LANG_LOCK = threading.Lock()
# {lang_name: last_translation_timestamp}
_lang_last_time = {}

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
        """Translate text. Returns the original text if translation fails or is rate-limited."""
        if not text or not text.strip():
            return ""

        # Per-language rate limiting (non-blocking — just skip)
        with _LANG_LOCK:
            last = _lang_last_time.get(target_lang, 0.0)
            if time.time() - last < _LANG_RATE_LIMIT:
                return ""  # skip — will be picked up next cycle

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
        callback(translated_text) when done. Skips if rate-limited."""
        if not text or not text.strip():
            return

        # Quick rate-limit check (may still race, but that's fine —
        # the worker loop will just send the same text again next cycle)
        with _LANG_LOCK:
            last = _lang_last_time.get(target_lang, 0.0)
            if time.time() - last < _LANG_RATE_LIMIT:
                return

        def _do_translate():
            try:
                result = self.translate(text, target_lang)
                if result:  # non-empty means it wasn't rate-limited
                    callback(result)
            except Exception as e:
                logger.error("Async translation error (%s): %s", target_lang, e)

        t = threading.Thread(target=_do_translate, daemon=True)
        t.start()
