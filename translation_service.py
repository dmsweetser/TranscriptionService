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
        if not text:
            return ""
        try:
            lang_code = LANG_CODE_MAP.get(target_lang, target_lang)
            return self.translator.translate(text, target=lang_code)
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return f"[Error: {str(e)}]"