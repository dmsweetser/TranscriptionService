import os

bind = f"0.0.0.0:{os.getenv('TRANSCRIPTION_PORT', '5123')}"
workers = int(os.getenv('GUNICORN_WORKERS', 4))
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
preload_app = False
max_requests = 1000
max_requests_jitter = 50
worker_class = 'sync'