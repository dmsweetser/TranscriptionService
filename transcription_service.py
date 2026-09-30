import assemblyai as aai
import numpy as np
import os
import logging
import time
import wave
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self):
        self.api_key = os.getenv("ASSEMBLY_AI_API_KEY")
        self.bias_words = [
            w.strip()
            for w in os.getenv("BIAS_WORDS", "").split(",")
            if w.strip()
        ]
        if not self.api_key:
            logger.warning(
                "Assembly AI API key not found. Transcription will be mocked."
            )
        self.transcriber = aai.Transcriber() if self.api_key else None

    def _mock_transcription(self):
        phrases = [
            "Hello world",
            "Testing transcription",
            "Production ready",
            "Mock data stream",
        ]
        return phrases[hash(time.time()) % len(phrases)]

    def transcribe_chunk(self, audio_data):
        """Transcribe a single numpy audio chunk. Returns a string."""
        if not self.api_key:
            return self._mock_transcription()

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as tmp:
                tmp_path = tmp.name
                with wave.open(tmp_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    if audio_data.dtype != np.int16:
                        audio_data = (
                            audio_data * 32767
                        ).astype(np.int16)
                    wf.writeframes(audio_data.tobytes())

            config = aai.TranscriptionConfig()
            if self.bias_words:
                config.set_word_boost(self.bias_words)

            transcript = self.transcriber.transcribe(
                tmp_path, config=config
            )
            os.unlink(tmp_path)
            return transcript.text if transcript and transcript.text else ""
        except Exception as e:
            logger.error("Transcription error: %s", e)
            return f"[Error: {e}]"

    def stream_transcription(self, audio_streamer):
        """Continuously collect audio chunks and transcribe them.

        Yields completed transcription text as it becomes available.
        """
        buffer = []
        chunk_size = audio_streamer.sample_rate  # ~1 second of audio
        while True:
            chunk = audio_streamer.get_audio_chunk()
            if chunk is not None:
                buffer.append(chunk)
                if len(buffer) >= chunk_size:
                    try:
                        combined = np.concatenate(buffer)
                        text = self.transcribe_chunk(combined)
                        buffer = []
                        if text:
                            yield text
                    except Exception as e:
                        logger.error("Buffer processing error: %s", e)
                        buffer = []
            else:
                time.sleep(0.05)
