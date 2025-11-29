import tempfile, requests, soundfile as sf, base64, numpy as np
import pyloudnorm as pyln
from flask import jsonify

def run_mastering(audio_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.wav")

        # Download audio
        r = requests.get(audio_url)
        with open(input_path, "wb") as f:
            f.write(r.content)

        audio, rate = sf.read(input_path)

        meter = pyln.Meter(rate)
        loud = meter.integrated_loudness(audio)

        normalized = pyln.normalize.loudness(audio, loud, -14.0)
        limited = np.clip(normalized, -0.99, 0.99)

        out_path = os.path.join(tmpdir, "master.wav")
        sf.write(out_path, limited, rate)

        with open(out_path, "rb") as f:
            master64 = base64.b64encode(f.read()).decode()

        return jsonify({
            "original_lufs": loud,
            "master": master64,
            "success": True
        })
