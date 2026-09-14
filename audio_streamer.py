import sounddevice as sd
import numpy as np
import queue
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioStreamer:
    def __init__(self, device_name=None, sample_rate=16000):
        self.sample_rate = sample_rate
        self.queue = queue.Queue()
        self.device = self._find_device(device_name)
        self.stream = None
        self.is_running = False
        self.thread = None

    def _find_device(self, device_name):
        devices = sd.query_devices()
        if device_name:
            for i, dev in enumerate(devices):
                if device_name.lower() in dev['name'].lower():
                    return i
        return sd.default.device[0]

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._record)
        self.thread.start()

    def _record(self):
        self.stream = sd.InputStream(
            device=self.device,
            channels=1,
            samplerate=self.sample_rate,
            callback=self._callback
        )
        self.stream.start()
        while self.is_running:
            sd.sleep(100)
        self.stream.stop()
        self.stream.close()

    def _callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"Stream status: {status}")
        if indata.size == 0:
            return
        data = indata.flatten()
        self.queue.put(data)

    def get_audio_chunk(self, timeout=1.0):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        self.is_running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if self.thread:
            self.thread.join(timeout=2.0)