import tempfile, os, base64, requests, librosa, numpy as np
from flask import jsonify
import crepe

def extract_melody(audio_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "audio.wav")

        # Download
        r = requests.get(audio_url)
        with open(path, "wb") as f:
            f.write(r.content)

        y, sr = librosa.load(path, sr=16000)

        # CREPE for pitch contour
        time, frequency, confidence, _ = crepe.predict(y, sr, viterbi=True)

        melody = {
            "time": time.tolist(),
            "frequency": frequency.tolist(),
            "confidence": confidence.tolist()
        }

        return jsonify({"melody": melody, "success": True})
