import os
import sys
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import argparse
import threading
import time
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('ADMIN_PASSWORD', 'default_secret_key')

# Mock data for demonstration
MOCK_AUDIO_DEVICES = [
    "Default Audio Device",
    "Microphone 1",
    "Microphone 2",
    "USB Audio Device"
]

MOCK_TRANSLATION_LANGUAGES = [
    "English",
    "French",
    "Spanish",
    "Arabic"
]

# Global state for service
service_running = False
transcription_data = []
translation_data = []
current_session_id = None

def start_service():
    global service_running
    service_running = True
    # In a real implementation, this would start the actual transcription service
    print("Service started")

def stop_service():
    global service_running
    service_running = False
    # In a real implementation, this would stop the actual transcription service
    print("Service stopped")

def generate_session_id():
    return f"session_{int(time.time())}"

def save_transcription(session_id, text):
    save_location = os.getenv("SAVE_LOCATION", "./transcriptions")
    os.makedirs(save_location, exist_ok=True)
    filename = os.path.join(save_location, f"{session_id}.txt")
    with open(filename, 'w') as f:
        f.write(text)

def get_transcription(session_id):
    save_location = os.getenv("SAVE_LOCATION", "./transcriptions")
    filename = os.path.join(save_location, f"{session_id}.txt")
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read()
    return ""

# Mock endpoints
@app.route('/mock/transcription', methods=['GET'])
def mock_transcription():
    return jsonify({"transcription": "This is a mock transcription."})

@app.route('/mock/translation', methods=['GET'])
def mock_translation():
    return jsonify({"translation": "This is a mock translation."})

@app.route('/mock/audio_devices', methods=['GET'])
def mock_audio_devices():
    return jsonify({"devices": MOCK_AUDIO_DEVICES})

@app.route('/mock/translation_languages', methods=['GET'])
def mock_translation_languages():
    return jsonify({"languages": MOCK_TRANSLATION_LANGUAGES})

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
    if password == os.getenv("ADMIN_PASSWORD"):
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
    # In a real implementation, this would update the configuration
    return jsonify({"status": "Configuration updated successfully"})

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
    args = parser.parse_args()
    
    if args.mock:
        print("Starting with mock endpoints enabled")
    
    app.run(debug=True, host='0.0.0.0', port=5456)