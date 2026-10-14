import os
import sys
import logging
import json
import time
import queue
import secrets
from flask import Flask, render_template, request, jsonify, session, Response, g
from flask_cors import CORS
from dotenv import load_dotenv
import bcrypt
import argparse
import threading

from audio_streamer import AudioStreamer
from transcription_service import TranscriptionService
from translation_service import TranslationService

# Load environment variables
load_dotenv()

# Configure logging for production
from logging.handlers import RotatingFileHandler
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "app.log")
os.makedirs(log_dir, exist_ok=True)

file_handler = RotatingFileHandler(
    log_file, maxBytes=10 * 1024 * 1024, backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)

logging.basicConfig(
    level=logging.INFO,
    handlers=[],
)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

app = Flask(__name__)

# CORS – allow the user-interface port and any QR-code-redirected origin
allowed_origins_raw = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5123,http://localhost:5001"
)
allowed_origins = [
    o.strip() for o in allowed_origins_raw.split(",") if o.strip()
]
CORS(
    app,
    resources={r"/*": {"origins": allowed_origins}},
    supports_credentials=True,
)

# Secret key – persist across restarts so sessions survive
_secret_key_path = os.path.join(log_dir, ".secret_key")
_raw_key = os.getenv("SECRET_KEY", "")
if _raw_key:
    app.secret_key = _raw_key
elif os.path.isfile(_secret_key_path):
    with open(_secret_key_path) as f:
        app.secret_key = f.read().strip()
else:
    app.secret_key = secrets.token_hex(32)
    with open(_secret_key_path, "w") as f:
        f.write(app.secret_key)


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ---------------------------------------------------------------------------
# Global state  (single-process, single-worker only)
# ---------------------------------------------------------------------------
audio_streamer = None
transcription_service = TranscriptionService()
translation_service = TranslationService()

service_running = False
service_thread = None
session_queues = {}          # session_id -> queue.Queue
session_lock = threading.Lock()
service_lock = threading.Lock()  # protects start/stop transitions

TRANSLATION_LANGUAGES = [
    "English", "French", "Spanish", "Arabic",
    "German", "Italian", "Japanese", "Korean",
]


# ---------------------------------------------------------------------------
# Audio devices
# ---------------------------------------------------------------------------
def get_audio_devices():
    """Return list of dicts {index, name, is_input}."""
    import sounddevice as sd
    devices = sd.query_devices()
    if isinstance(devices, dict):
        # sounddevice sometimes returns a single dict for default device
        return [{"index": 0, "name": devices.get("name", "Default")}]
    result = []
    for i, dev in enumerate(devices):
        if isinstance(dev, dict):
            result.append({"index": i, "name": dev.get("name", f"Device {i}")})
        else:
            result.append({"index": i, "name": str(dev)})
    return result


# ---------------------------------------------------------------------------
# Service lifecycle
# ---------------------------------------------------------------------------
def start_service():
    """Start the transcription/translation pipeline. Thread-safe."""
    global service_running, service_thread, audio_streamer

    with service_lock:
        if service_running:
            logger.info("Service is already running")
            return "Service is already running"

        device_name = os.getenv("DEFAULT_AUDIO_DEVICE", "Default Audio Device")
        try:
            audio_streamer = AudioStreamer(device_name=device_name)
            audio_streamer.start()
        except Exception as e:
            logger.error("Failed to start audio streamer: %s", e)
            return f"Failed to start audio streamer: {e}"

        service_running = True

        def worker():
            global service_running
            try:
                if not audio_streamer:
                    logger.error("Audio streamer not initialized")
                    return
                for text in transcription_service.stream_transcription(
                    audio_streamer
                ):
                    if not service_running:
                        break
                    logger.info("Transcription: %s", text)
                    # Broadcast transcription to all sessions
                    with session_lock:
                        for q in session_queues.values():
                            try:
                                q.put_nowait(
                                    {"type": "transcription", "text": text}
                                )
                            except Exception:
                                pass

                    # Translate and broadcast per-language
                    for lang in TRANSLATION_LANGUAGES:
                        translated = translation_service.translate(text, lang)
                        with session_lock:
                            for q in session_queues.values():
                                try:
                                    q.put_nowait(
                                        {
                                            "type": "translation",
                                            "lang": lang,
                                            "text": translated,
                                        }
                                    )
                                except Exception:
                                    pass
            except Exception as e:
                logger.error("Service worker error: %s", e)
            finally:
                service_running = False

        service_thread = threading.Thread(target=worker, daemon=True)
        service_thread.start()
        logger.info("Service started")
        return None  # success


def stop_service():
    """Stop the transcription/translation pipeline. Thread-safe."""
    global service_running, audio_streamer

    with service_lock:
        if not service_running:
            return "Service is not running"

        service_running = False
        if audio_streamer:
            try:
                audio_streamer.stop()
            except Exception as e:
                logger.error("Error stopping audio streamer: %s", e)
            audio_streamer = None

        # Drain session queues
        with session_lock:
            session_queues.clear()

        logger.info("Service stopped")
        return None  # success


def generate_session_id():
    return f"session_{int(time.time())}_{secrets.token_urlsafe(16)}"


# ---------------------------------------------------------------------------
# Transcription persistence
# ---------------------------------------------------------------------------
def save_transcription(session_id, text):
    save_location = os.getenv("SAVE_LOCATION", "./transcriptions")
    os.makedirs(save_location, exist_ok=True)
    filename = os.path.join(save_location, f"{session_id}.txt")
    with open(filename, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")


def get_transcription(session_id):
    save_location = os.getenv("SAVE_LOCATION", "./transcriptions")
    filename = os.path.join(save_location, f"{session_id}.txt")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return f.read()
    return ""


# ---------------------------------------------------------------------------
# Config persistence  (rewrites .env)
# ---------------------------------------------------------------------------
def persist_config(config):
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    existing = {}
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()

    # Values to persist
    env_vars = {
        "ASSEMBLYAI_API_KEY": config.get("ASSEMBLYAI_API_KEY", ""),
        "DEFAULT_AUDIO_DEVICE": config.get("audio_device", "Default Audio Device"),
        "TRANSCRIPTION_PORT": str(config.get("transcription_port", 5123)),
        "TRANSLATION_PORT": str(config.get("translation_port", 5001)),
        "BIAS_WORDS": ",".join(
            w.strip() for w in config.get("bias_words", []) if w.strip()
        ),
        "SAVE_LOCATION": config.get("save_location", "./transcriptions"),
    }
    # Preserve password hash / secret key if not being changed
    if config.get("admin_password_hash"):
        env_vars["ADMIN_PASSWORD_HASH"] = config["admin_password_hash"]
    elif "ADMIN_PASSWORD_HASH" in existing:
        env_vars["ADMIN_PASSWORD_HASH"] = existing["ADMIN_PASSWORD_HASH"]

    if config.get("secret_key"):
        env_vars["SECRET_KEY"] = config["secret_key"]
    elif "SECRET_KEY" in existing:
        env_vars["SECRET_KEY"] = existing["SECRET_KEY"]

    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

    # Reload into os.environ
    load_dotenv(env_path, override=True)


# ---------------------------------------------------------------------------
# Routes – public
# ---------------------------------------------------------------------------
@app.route("/health")
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "service_running": service_running,
            "sessions_active": len(session_queues),
        }
    ), 200


@app.route("/")
def index():
    return render_template("user_interface.html")


# ---------------------------------------------------------------------------
# Routes – admin
# ---------------------------------------------------------------------------
@app.route("/admin")
def admin():
    if "authenticated" not in session:
        return render_template("admin_login.html")
    return render_template("admin_interface.html")


@app.route("/admin/auth", methods=["POST"])
def authenticate():
    password = request.json.get("password", "")
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH", "")

    if stored_hash:
        try:
            if bcrypt.checkpw(
                password.encode("utf-8"), stored_hash.encode("utf-8")
            ):
                session["authenticated"] = True
                return jsonify({"authenticated": True})
        except Exception as e:
            logger.error("Auth error: %s", e)
            return jsonify({"error": "Authentication service error"}), 500
    else:
        # Legacy plain-text fallback – log a warning
        plain = os.getenv("ADMIN_PASSWORD", "")
        if plain and password == plain:
            logger.warning(
                "Using legacy plain-text password. "
                "Run setup_admin.py to migrate to hashed password."
            )
            session["authenticated"] = True
            return jsonify({"authenticated": True})

    return jsonify({"authenticated": False}), 401


@app.route("/admin/logout", methods=["POST"])
def logout():
    session.pop("authenticated", None)
    return jsonify({"status": "Logged out"})


@app.route("/admin/config", methods=["GET"])
def admin_config():
    if "authenticated" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(
        {
            "audio_device": os.getenv("DEFAULT_AUDIO_DEVICE", "Default Audio Device"),
            "transcription_port": os.getenv("TRANSCRIPTION_PORT", "5123"),
            "translation_port": os.getenv("TRANSLATION_PORT", "5001"),
            "bias_words": [
                w.strip()
                for w in os.getenv("BIAS_WORDS", "").split(",")
                if w.strip()
            ],
            "save_location": os.getenv("SAVE_LOCATION", "./transcriptions"),
            "ASSEMBLYAI_API_KEY": os.getenv("ASSEMBLYAI_API_KEY", ""),
            "service_running": service_running,
        }
    )


@app.route("/admin/config", methods=["POST"])
def update_config():
    if "authenticated" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    config = request.json
    try:
        persist_config(config)
        logger.info("Configuration updated and persisted")
        return jsonify({"status": "Configuration updated successfully"})
    except Exception as e:
        logger.error("Config update error: %s", e)
        return jsonify({"error": "Failed to update configuration"}), 500


@app.route("/admin/service", methods=["POST"])
def control_service():
    if "authenticated" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    action = request.json.get("action", "")
    if action == "start":
        err = start_service()
        if err:
            return jsonify({"error": err}), 500
        return jsonify({"status": "Service started"})
    elif action == "stop":
        err = stop_service()
        if err:
            return jsonify({"error": err}), 500
        return jsonify({"status": "Service stopped"})
    return jsonify({"error": "Invalid action"}), 400


@app.route("/admin/connections", methods=["GET"])
def get_connections():
    if "authenticated" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(
        {
            "internal": [
                {"name": "Assembly AI API", "status": "ok"},
                {"name": "Transcription Service", "status": "ok"},
                {"name": "Translation Service", "status": "ok"},
            ],
            "external": [
                {
                    "name": f"User Interface {i}",
                    "status": "connected" if service_running else "disconnected",
                }
                for i in range(1, len(session_queues) + 1)
            ]
            or [{"name": "No active connections", "status": "disconnected"}],
        }
    )


@app.route("/admin/audio_devices", methods=["GET"])
def admin_audio_devices():
    if "authenticated" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"devices": get_audio_devices()})


# ---------------------------------------------------------------------------
# Routes – user streams
# ---------------------------------------------------------------------------
@app.route("/api/audio_devices", methods=["GET"])
def get_audio_devices_public():
    return jsonify({"devices": get_audio_devices()})


@app.route("/api/translation_languages", methods=["GET"])
def get_translation_languages():
    return jsonify({"languages": TRANSLATION_LANGUAGES})


@app.route("/api/transcription/stream", methods=["GET"])
def transcription_stream():
    session_id = generate_session_id()
    q = queue.Queue()
    with session_lock:
        session_queues[session_id] = q
    try:
        def generate():
            while True:
                try:
                    data = q.get(timeout=30)
                    if data is None:
                        break
                    yield f"data: {json.dumps(data)}\n\n"
                except queue.Empty:
                    # Send keepalive to prevent timeout
                    yield ": keepalive\n\n"
        return Response(generate(), mimetype="text/event-stream")
    except GeneratorExit:
        with session_lock:
            session_queues.pop(session_id, None)
        logger.info("Transcription stream closed: %s", session_id)


@app.route("/api/translation/stream/<lang>", methods=["GET"])
def translation_stream(lang):
    session_id = generate_session_id()
    q = queue.Queue()
    with session_lock:
        session_queues[session_id] = q
    try:
        def generate():
            while True:
                try:
                    data = q.get(timeout=30)
                    if data is None:
                        break
                    if (
                        data.get("type") == "translation"
                        and data.get("lang") == lang
                    ):
                        yield f"data: {json.dumps(data)}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        return Response(generate(), mimetype="text/event-stream")
    except GeneratorExit:
        with session_lock:
            session_queues.pop(session_id, None)
        logger.info("Translation stream closed: %s", session_id)


# ---------------------------------------------------------------------------
# Signal handlers (for direct python app.py execution, NOT gunicorn)
# ---------------------------------------------------------------------------
import signal
import atexit


def _shutdown():
    logger.info("Shutdown signal received. Stopping service...")
    stop_service()


atexit.register(_shutdown)


def _handle_signal(signum, frame):
    logger.info("Signal %d received. Stopping service...", signum)
    stop_service()


# Only register for direct execution (gunicorn handles its own signals)
if __name__ == "__main__" or "GUNICORN" not in os.environ:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TranscriptionService")
    parser.add_argument(
        "--mock", action="store_true", help="Enable mock endpoints"
    )
    parser.add_argument(
        "--port", type=int, default=5123, help="Port to run on"
    )
    args = parser.parse_args()

    if args.mock:
        logger.warning(
            "Running in mock mode. Real functionality requires API keys."
        )

    app.run(debug=args.mock, host="0.0.0.0", port=args.port)
