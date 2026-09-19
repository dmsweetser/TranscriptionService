import os

bind = f"0.0.0.0:{os.getenv('TRANSCRIPTION_PORT', '5123')}"
# Production requires a single worker for global state (audio streamer, service threads)
# Multi-worker would duplicate the audio streamer and cause race conditions.
workers = int(os.getenv('GUNICORN_WORKERS', 1))
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
preload_app = False
max_requests = 1000
max_requests_jitter = 50
worker_class = 'sync'