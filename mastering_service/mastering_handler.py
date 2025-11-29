import os
import tempfile
import requests
import soundfile as sf
import numpy as np
import pyloudnorm as pyln


def run_mastering(audio_url):
    """
    Input: audio_url
    Output: raw WAV bytes (not JSON)
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.wav")

        # ------------------------------
        # 1. Download audio
        # ------------------------------
        with open(input_path, "wb") as f:
            f.write(requests.get(audio_url).content)

        # ------------------------------
        # 2. Load audio
        # ------------------------------
        audio, rate = sf.read(input_path)

        # Ensure float32
        audio = audio.astype(np.float32)

        # ------------------------------
        # 3. Measure loudness
        # ------------------------------
        meter = pyln.Meter(rate)
        original_lufs = meter.integrated_loudness(audio)

        # ------------------------------
        # 4. Normalize to target LUFS
        # ------------------------------
        target_lufs = -14.0
        normalized = pyln.normalize.loudness(audio, original_lufs, target_lufs)

        # Keep values in safe range
        normalized = np.clip(normalized, -0.99, 0.99).astype(np.float32)

        # ------------------------------
        # 5. Write mastered file
        # ------------------------------
        output_path = os.path.join(tmpdir, "master.wav")
        sf.write(output_path, normalized, rate)

        # ------------------------------
        # 6. Return raw bytes
        # ------------------------------
        with open(output_path, "rb") as f:
            return f.read()
