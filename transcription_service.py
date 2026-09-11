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
            for _ in audio_chunks:
                yield self._mock_transcription([])
            return
        
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
                with wave.open(tmp_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    if isinstance(audio_chunks, np.ndarray):
                        wf.writeframes(audio_chunks.tobytes())
                    else:
                        for chunk in audio_chunks:
                            wf.writeframes(chunk.tobytes())
            config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
            transcript = self.transcriber.transcribe(tmp_path, config)
            os.unlink(tmp_path)
            yield transcript.text if transcript else ""
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            yield f"[Error: {str(e)}]"

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