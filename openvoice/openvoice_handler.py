from flask import jsonify
import base64
from openvoice import TTS

def run_openvoice(text):
    tts = TTS(model_path="./openvoice/models/vale.pth")

    wav = tts.tts(text)
    audio_bytes = wav.tobytes()
    audio64 = base64.b64encode(audio_bytes).decode()

    return jsonify({"audio": audio64, "success": True})
