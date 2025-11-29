import os
from openvoice_cli import TTS
import tempfile
from flask import jsonify

def run_openvoice(reference_url, text):
    tts = TTS()

    result_path = tts.infer(
        reference_audio=reference_url,
        prompt=text,
    )

    with open(result_path, "rb") as f:
        data = f.read()

    return jsonify({
        "audio_base64": base64.b64encode(data).decode()
    })
