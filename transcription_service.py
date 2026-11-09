import assemblyai as aai
import numpy as np
import os
import logging
import time
import wave
import tempfile

logger = logging.getLogger("app.transcription")


class TranscriptionService:
    def __init__(self):
        self.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        self.bias_words = [
            w.strip()
            for w in os.getenv("BIAS_WORDS", "").split(",")
            if w.strip()
        ]
        logger.info("TranscriptionService init: api_key set=%s, key_len=%s",
                     bool(self.api_key), len(self.api_key) if self.api_key else 0)
        if not self.api_key or self.api_key == "***":
            logger.warning(
                "Assembly AI API key not set. Transcription will be mocked."
            )
            self.transcriber = None
        else:
            try:
                import assemblyai as aai
                aai.settings.api_key = self.api_key
                self.transcriber = aai.Transcriber()
                if self.transcriber is None:
                    raise ValueError("Transcriber returned None")
                logger.info("AssemblyAI transcriber created successfully")
            except Exception as e:
                logger.warning(
                    "Failed to create AssemblyAI transcriber (%s). "
                    "Transcription will be mocked.", e
                )
                self.transcriber = None

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
        if not self.transcriber:
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
        Deduplicates: only yields text when it actually changes from the
        previous result, preventing redundant translation calls.
        """
        buffer = []
        target_samples = int(audio_streamer.sample_rate * 0.5)  # ~0.5s buffer
        last_text = ""
        while True:
            chunk = audio_streamer.get_audio_chunk(timeout=0.5)
            if chunk is not None:
                buffer.append(chunk)
                total_samples = sum(c.shape[0] for c in buffer)
                if total_samples >= target_samples:
                    try:
                        combined = np.concatenate(buffer)
                        text = self.transcribe_chunk(combined)
                        buffer = []
                        # Deduplicate: only yield if text actually changed
                        if text and text != last_text:
                            last_text = text
                            yield text
                    except Exception as e:
                        logger.error("Buffer processing error: %s", e)
                        buffer = []
            else:
                time.sleep(0.05)
