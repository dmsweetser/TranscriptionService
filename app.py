import os
import sys
import logging
import json
import time
import queue
from flask import Flask, render_template, request, jsonify, session, Response
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))

# Initialize services
audio_streamer = None
transcription_service = TranscriptionService()
translation_service = TranslationService()

# Global state
service_running = False
service_thread = None
session_queues = {}
session_lock = threading.Lock()

# Audio device list from sounddevice
def get_audio_devices():
    import sounddevice as sd
    devices = sd.query_devices()
    return [dev['name'] for dev in devices]

# Translation languages
TRANSLATION_LANGUAGES = ["English", "French", "Spanish", "Arabic", "German", "Italian", "Japanese", "Korean"]

def start_service():
    global service_running, service_thread, audio_streamer
    if service_running:
        return
    service_running = True
    device_name = os.getenv("DEFAULT_AUDIO_DEVICE")
    audio_streamer = AudioStreamer(device_name=device_name)
    audio_streamer.start()
    
    def worker():
        global service_running
        try:
            for text in transcription_service.stream_transcription(audio_streamer):
                logger.info(f"Transcription: {text}")
                with session_lock:
                    for q in session_queues.values():
                        q.put({"type": "transcription", "text": text})
                
                for lang in TRANSLATION_LANGUAGES:
                    translated = translation_service.translate(text, lang)
                    with session_lock:
                        for q in session_queues.values():
                            q.put({"type": "translation", "lang": lang, "text": translated})
        except Exception as e:
            logger.error(f"Service worker error: {e}")
        finally:
            service_running = False

    service_thread = threading.Thread(target=worker, daemon=True)
    service_thread.start()
    logger.info("Service started")

def stop_service():
    global service_running, audio_streamer
    if not service_running:
        return
    service_running = False
    if audio_streamer:
        audio_streamer.stop()
    logger.info("Service stopped")

def generate_session_id():
    return f"session_{int(time.time())}_{os.urandom(4).hex()}"

def save_transcription(session_id, text):
    save_location = os.getenv("SAVE_LOCATION", "./transcriptions")
    os.makedirs(save_location, exist_ok=True)
    filename = os.path.join(save_location, f"{session_id}.txt")
    with open(filename, 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")

def get_transcription(session_id):
    save_location = os.getenv("SAVE_LOCATION", "./transcriptions")
    filename = os.path.join(save_location, f"{session_id}.txt")
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read()
    return ""

def persist_config(config):
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    with open(env_path, 'w') as f:
        f.write(f"DEFAULT_AUDIO_DEVICE={config.get('audio_device', 'Default Audio Device')}\n")
        f.write(f"TRANSCRIPTION_PORT={config.get('transcription_port', 5123)}\n")
        f.write(f"TRANSLATION_PORT={config.get('translation_port', 5001)}\n")
        f.write(f"BIAS_WORDS={','.join(config.get('bias_words', []))}\n")
        f.write(f"SAVE_LOCATION={config.get('save_location', './transcriptions')}\n")
    load_dotenv(env_path)

@app.route('/api/audio_devices', methods=['GET'])
def get_audio_devices():
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"devices": get_audio_devices()})

@app.route('/api/translation_languages', methods=['GET'])
def get_translation_languages():
    return jsonify({"languages": TRANSLATION_LANGUAGES})

@app.route('/api/transcription/stream', methods=['GET'])
def transcription_stream():
    session_id = generate_session_id()
    q = queue.Queue()
    with session_lock:
        session_queues[session_id] = q
    try:
        def generate():
            while True:
                data = q.get()
                if data is None:
                    break
                yield f"data: {json.dumps(data)}\n\n"
        return Response(generate(), mimetype='text/event-stream')
    except GeneratorExit:
        with session_lock:
            session_queues.pop(session_id, None)

@app.route('/api/translation/stream/<lang>', methods=['GET'])
def translation_stream(lang):
    session_id = generate_session_id()
    q = queue.Queue()
    with session_lock:
        session_queues[session_id] = q
    try:
        def generate():
            while True:
                data = q.get()
                if data is None:
                    break
                if data.get('type') == 'translation' and data.get('lang') == lang:
                    yield f"data: {json.dumps(data)}\n\n"
        return Response(generate(), mimetype='text/event-stream')
    except GeneratorExit:
        with session_lock:
            session_queues.pop(session_id, None)

@app.route('/')
def index():
    return render_template('user_interface.html')

@app.route('/admin')
def admin():
    if 'authenticated' not in session:
        return render_template('admin_login.html')
    return render_template('admin_interface.html')

@app.route('/admin/auth', methods=['POST'])
def authenticate():
    password = request.json.get('password')
    stored_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if not stored_hash:
        # Fallback for initial setup
        if password == os.getenv("ADMIN_PASSWORD"):
            session['authenticated'] = True
            return jsonify({"authenticated": True})
        return jsonify({"authenticated": False}), 401
    
    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        session['authenticated'] = True
        return jsonify({"authenticated": True})
    return jsonify({"authenticated": False}), 401

@app.route('/admin/logout', methods=['POST'])
def logout():
    session.pop('authenticated', None)
    return jsonify({"status": "Logged out"})

@app.route('/admin/config', methods=['GET'])
def admin_config():
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "audio_device": os.getenv("DEFAULT_AUDIO_DEVICE", "Default Audio Device"),
        "transcription_port": os.getenv("TRANSCRIPTION_PORT", 5000),
        "translation_port": os.getenv("TRANSLATION_PORT", 5001),
        "bias_words": os.getenv("BIAS_WORDS", "").split(","),
        "save_location": os.getenv("SAVE_LOCATION", "./transcriptions")
    })

@app.route('/admin/config', methods=['POST'])
def update_config():
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    config = request.json
    try:
        persist_config(config)
        logger.info("Configuration updated and persisted")
        return jsonify({"status": "Configuration updated successfully"})
    except Exception as e:
        logger.error(f"Config update error: {e}")
        return jsonify({"error": "Failed to update configuration"}), 500

@app.route('/admin/service', methods=['POST'])
def control_service():
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    action = request.json.get('action')
    if action == 'start':
        start_service()
        return jsonify({"status": "Service started"})
    elif action == 'stop':
        stop_service()
        return jsonify({"status": "Service stopped"})
    return jsonify({"error": "Invalid action"}), 400

@app.route('/admin/connections', methods=['GET'])
def get_connections():
    if 'authenticated' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "internal": [
            "Assembly AI API",
            "Transcription Service",
            "Translation Service"
        ],
        "external": [
            "User Interface 1",
            "User Interface 2"
        ]
    })

@app.route('/transcription/<session_id>', methods=['GET'])
def get_transcription_stream(session_id):
    text = get_transcription(session_id)
    return jsonify({"transcription": text})

@app.route('/translation/<session_id>/<language>', methods=['GET'])
def get_translation_stream(session_id, language):
    # In a real implementation, this would return the translation for the specified language
    return jsonify({"translation": f"Translation for {language} in session {session_id}"})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TranscriptionService')
    parser.add_argument('--mock', action='store_true', help='Enable mock endpoints')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    args = parser.parse_args()
    
    if args.mock:
        logger.warning("Running in mock mode. Real functionality requires API keys.")
    
    app.run(debug=args.mock, host='0.0.0.0', port=args.port)