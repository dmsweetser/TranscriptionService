from deep_translator import GoogleTranslator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='en')

    def translate(self, text, target_lang='en'):
        if not text:
            return ""
        try:
            return self.translator.translate(text, target_lang)
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return f"[Error: {str(e)}]"