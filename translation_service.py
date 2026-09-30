from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)

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
        pass

    def translate(self, text, target_lang="en"):
        if not text or not text.strip():
            return ""
        try:
            lang_code = LANG_CODE_MAP.get(target_lang, target_lang)
            translator = GoogleTranslator(source="auto", target=lang_code)
            translated = translator.translate(text)
            return translated if translated else text
        except Exception as e:
            logger.error("Translation error: %s", e)
            return text
