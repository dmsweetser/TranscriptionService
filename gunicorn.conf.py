import os

bind = f"0.0.0.0:{os.getenv('TRANSCRIPTION_PORT', '5123')}"
workers = 4
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"