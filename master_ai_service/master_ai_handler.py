import os
import tempfile
import requests
import subprocess
import numpy as np
import soundfile as sf
import librosa
import pyloudnorm as pyln
import scipy.signal as signal


# ------------------------------------------------------------
# FAST MODE — Loudnorm + FFmpeg Limiter
# ------------------------------------------------------------
def _master_fast(audio_url):
    input_path = tempfile.mktemp(suffix=".wav")
    output_path = tempfile.mktemp(suffix=".wav")

    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    # Simple loudnorm
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af", "loudnorm=I=-12:TP=-1:LRA=7",
        output_path
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with open(output_path, "rb") as f:
        return f.read()


# ------------------------------------------------------------
# HQ MODE — AI-Style Mastering Chain (CPU DSP)
# ------------------------------------------------------------
def _master_hq(audio_url):
    """
    HQ Mastering:
    - multi-band EQ
    - saturation
    - multiband compression
    - true-peak limiting
    """

    # ---------------------------
    # 1. Download + Load Audio
    # ---------------------------
    input_path = tempfile.mktemp(suffix=".wav")

    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    y, sr = librosa.load(input_path, sr=44100)

    # Convert to float32
    y = y.astype(np.float32)


    # ---------------------------
    # 2. Multi-band EQ
    # ---------------------------
    # Low-end tightening (around 80–120 Hz)
    low = librosa.effects.bandpass(y, sr=sr, low=60, high=180)
    low *= 0.85

    # Low-mids cleanup (mud reduction 200–400 Hz)
    lowmid = librosa.effects.bandpass(y, sr=sr, low=200, high=400)
    lowmid *= 0.75

    # Presence boost (3 kHz region)
    hi_mid = librosa.effects.bandpass(y, sr=sr, low=2500, high=4500)
    hi_mid *= 1.25

    # Air shelf (10–12 kHz)
    air = librosa.effects.bandpass(y, sr=sr, low=8000, high=14000)
    air *= 1.35

    # Reconstruct EQ curve
    eq_master = (
        (y * 0.75) +
        (low * 0.15) +
        (lowmid * 0.10) +
        (hi_mid * 0.20) +
        (air * 0.25)
    )


    # ---------------------------
    # 3. Soft Tape Saturation
    # ---------------------------
    sat = np.tanh(eq_master * 2.0) * 0.7 + eq_master * 0.3


    # ---------------------------
    # 4. Multi-band compression
    # ---------------------------
    def compress_band(band, amount=0.7):
        thr = 0.6 * np.max(np.abs(band))
        comp = np.where(
            np.abs(band) > thr,
            thr + (np.abs(band) - thr) * amount,
            band
        )
        return comp * np.sign(band)

    low_c = compress_band(low, amount=0.5)
    mid_c = compress_band(lowmid, amount=0.6)
    high_c = compress_band(hi_mid, amount=0.65)
    air_c = compress_band(air, amount=0.7)

    multi_comp = (
        sat * 0.6 +
        low_c * 0.2 +
        mid_c * 0.2 +
        high_c * 0.25 +
        air_c * 0.3
    )


    # ---------------------------
    # 5. True Peak Limiter
    # ---------------------------
    maxamp = max(1e-8, np.max(np.abs(multi_comp)))
    limited = (multi_comp / maxamp) * 0.98


    # ---------------------------
    # 6. Loudness Normalization (pyloudnorm)
    # ---------------------------
    meter = pyln.Meter(sr)
    loud = meter.integrated_loudness(limited)

    target_lufs = -10.5  # modern metalcore target
    loud_norm = pyln.normalize.loudness(limited, loud, target_lufs)

    # Safety clip
    loud_norm = np.clip(loud_norm, -1.0, 1.0).astype(np.float32)


    # ---------------------------
    # 7. Write Mastered File
    # ---------------------------
    out_path = tempfile.mktemp(suffix=".wav")
    sf.write(out_path, loud_norm, sr)

    with open(out_path, "rb") as f:
        return f.read()


# ------------------------------------------------------------
# PUBLIC ENTRYPOINT (called by app.py)
# ------------------------------------------------------------
def run_master_ai(audio_url, preset=None):
    """
    preset='default' → fast mode
    preset='hq' OR ?quality=hq → HQ AI mastering
    """
    # Determine if HQ requested via preset or query args
    if isinstance(preset, str):
        if preset.lower() in ["hq", "librosa", "true", "1", "master"]:
            return _master_hq(audio_url)

    # Default fast mode
    return _master_fast(audio_url)
