import os
import sys
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()

app = Flask(__name__)

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
    return render_template('admin_interface.html')

@app.route('/admin/config', methods=['GET'])
def admin_config():
    return jsonify({
        "audio_device": os.getenv("DEFAULT_AUDIO_DEVICE", "Default Audio Device"),
        "transcription_port": os.getenv("TRANSCRIPTION_PORT", 5000),
        "translation_port": os.getenv("TRANSLATION_PORT", 5001),
        "bias_words": os.getenv("BIAS_WORDS", "").split(","),
        "save_location": os.getenv("SAVE_LOCATION", "./transcriptions")
    })

@app.route('/admin/config', methods=['POST'])
def update_config():
    # In a real implementation, this would update the configuration
    return jsonify({"status": "Configuration updated successfully"})

@app.route('/admin/auth', methods=['POST'])
def authenticate():
    password = request.json.get('password')
    if password == os.getenv("ADMIN_PASSWORD"):
        return jsonify({"authenticated": True})
    return jsonify({"authenticated": False}), 401

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TranscriptionService')
    parser.add_argument('--mock', action='store_true', help='Enable mock endpoints')
    args = parser.parse_args()
    
    if args.mock:
        print("Starting with mock endpoints enabled")
    
    app.run(debug=True, host='0.0.0.0', port=5000)