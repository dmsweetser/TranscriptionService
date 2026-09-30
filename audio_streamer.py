import sounddevice as sd
import numpy as np
import queue
import threading
import logging

logger = logging.getLogger(__name__)


class AudioStreamer:
    def __init__(self, device_name=None, sample_rate=16000):
        self.sample_rate = sample_rate
        self.queue = queue.Queue(maxsize=10)
        self.device_index = self._find_device(device_name)
        self.stream = None
        self.is_running = False
        self.thread = None

    def _find_device(self, device_name):
        if not device_name or device_name.strip() in ("", "Default Audio Device"):
            return sd.default.device[0]
        name_lower = device_name.lower()
        try:
            all_devices = sd.query_devices()
        except Exception:
            all_devices = []
        if isinstance(all_devices, list):
            for i, dev in enumerate(all_devices):
                dev_name = dev.get("name", "") if isinstance(dev, dict) else str(dev)
                if name_lower in dev_name.lower():
                    return i
        logger.warning(
            "Device '%s' not found, using default", device_name
        )
        return sd.default.device[0]

    def start(self):
        self.is_running = True
        self.stream = sd.InputStream(
            device=self.device_index,
            channels=1,
            samplerate=self.sample_rate,
            callback=self._callback,
        )
        self.stream.start()
        self.thread = threading.Thread(target=self._keep_alive, daemon=True)
        self.thread.start()

    def _keep_alive(self):
        while self.is_running:
            sd.sleep(100)
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()

    def _callback(self, indata, frames, time, status):
        if status:
            logger.warning("Stream status: %s", status)
        if indata.size == 0:
            return
        try:
            data = indata.flatten().copy()
            self.queue.put_nowait(data)
        except queue.Full:
            logger.warning("Audio queue full, dropping chunk")

    def get_audio_chunk(self, timeout=1.0):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=3.0)
        if self.stream:
            try:
                if self.stream.active:
                    self.stream.stop()
                self.stream.close()
            except Exception:
                pass
