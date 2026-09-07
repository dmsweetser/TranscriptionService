import assemblyai as aai
import numpy as np
import os
import logging
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        self.api_key = os.getenv("ASSEMBLY_AI_API_KEY")
        if not self.api_key:
            logger.warning("Assembly AI API key not found. Transcription will be mocked.")
        self.transcriber = aai.Transcriber() if self.api_key else None

    def transcribe_stream(self, audio_chunks):
        if not self.api_key:
            return self._mock_transcription(audio_chunks)
        
        try:
            config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
            transcript = self.transcriber.transcribe(audio_chunks, config)
            return transcript.text if transcript else ""
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return f"[Error: {str(e)}]"

    def _mock_transcription(self, chunks):
        phrases = ["Hello world", "Testing transcription", "Production ready", "Mock data stream"]
        return random.choice(phrases)

    def stream_transcription(self, audio_streamer):
        buffer = []
        chunk_size = audio_streamer.sample_rate
        while True:
            chunk = audio_streamer.get_audio_chunk()
            if chunk is not None:
                buffer.append(chunk)
                if len(buffer) >= chunk_size:
                    text = self.transcribe_stream(np.concatenate(buffer))
                    buffer = []
                    if text:
                        yield text
            else:
                time.sleep(0.1)