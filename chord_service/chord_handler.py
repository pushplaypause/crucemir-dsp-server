import tempfile, os, requests, base64
from flask import jsonify
import librosa
import numpy as np

def detect_chords(audio_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "input.wav")

        r = requests.get(audio_url)
        with open(path, "wb") as f:
            f.write(r.content)

        y, sr = librosa.load(path)

        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        chord = np.argmax(chroma_mean)

        chord_map = [
            "C", "C#", "D", "D#", "E", "F",
            "F#", "G", "G#", "A", "A#", "B"
        ]

        return jsonify({"chord": chord_map[chord], "success": True})
