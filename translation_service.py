from deep_translator import GoogleTranslator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANG_CODE_MAP = {
    "English": "en",
    "French": "fr",
    "Spanish": "es",
    "Arabic": "ar",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko"
}

class TranslationService:
    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='en')

    def translate(self, text, target_lang='en'):
        if not text or not text.strip():
            return ""
        try:
            lang_code = LANG_CODE_MAP.get(target_lang, target_lang)
            translated = self.translator.translate(text, target=lang_code)
            return translated if translated else text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text