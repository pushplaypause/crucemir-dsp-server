from flask import jsonify
import base64
from sovits import SoVITS

def run_sovits(lyrics, melody_midi):
    model = SoVITS("./sovits/models/vale_singing.pth")

    audio = model.sing(lyrics, melody_midi)
    audio_bytes = audio.tobytes()

    return jsonify({
        "audio": base64.b64encode(audio_bytes).decode(),
        "success": True
    })
