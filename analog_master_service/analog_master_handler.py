import tempfile
import requests
import numpy as np
import soundfile as sf
import librosa
import scipy.signal as signal
import subprocess


# ------------------------------------------------------------
# FAST MODE (existing FFmpeg)
# ------------------------------------------------------------
def _analog_fast(audio_url):
    """
    Fast 'analog-like' chain using FFmpeg filters.
    Very lightweight.
    """
    input_path = tempfile.mktemp(suffix=".wav")
    out_path = tempfile.mktemp(suffix=".wav")

    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af",
        (
            "bass=g=3,"
            "treble=g=-2,"
            "acompressor=threshold=-15dB:ratio=3:attack=10:release=50,"
            "crystalizer=strength=0.3"
        ),
        out_path
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with open(out_path, "rb") as f:
        return f.read()


# ------------------------------------------------------------
# HQ MODE — True Analog Tape + Tube Modeling
# ------------------------------------------------------------
def _analog_hq(audio_url):
    """
    HQ Analog Mastering:
    - Tape soft-knee saturation
    - Tube harmonics
    - Crosstalk stereo widening
    - Analog-style EQ
    - Warm smooth limiter
    """

    # --------------------------------
    # 1. Download + load
    # --------------------------------
    input_path = tempfile.mktemp(suffix=".wav")
    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    y, sr = librosa.load(input_path, sr=44100)
    y = y.astype(np.float32)

    # --------------------------------
    # 2. ANLOG EQ CURVES
    # --------------------------------
    # Vintage low bump (60–120 Hz)
    low_bump = librosa.effects.bandpass(y, sr=sr, low=60, high=180) * 1.25

    # Gentle mid scoop (300–700 Hz)
    mid_scoop = librosa.effects.bandpass(y, sr=sr, low=300, high=800) * 0.8

    # Smooth high roll-off (tape style)
    highs = librosa.effects.bandpass(y, sr=sr, low=6000, high=16000) * 0.65

    eq = (
        y * 0.75 +
        low_bump * 0.20 +
        mid_scoop * 0.05 +
        highs * 0.15
    )

    # --------------------------------
    # 3. TAPE SATURATION (soft knee)
    # --------------------------------
    tape = np.tanh(eq * 1.8) * 0.7 + eq * 0.3

    # --------------------------------
    # 4. TUBE HARMONICS
    # --------------------------------
    tube = eq + 0.15 * (eq ** 3)  # gentle 3rd harmonic
    tube = tube / max(1e-6, np.max(np.abs(tube)))

    # --------------------------------
    # 5. Combine analog chain
    # --------------------------------
    analog = (
        eq * 0.55 +
        tape * 0.30 +
        tube * 0.25
    )

    # --------------------------------
    # 6. Stereo Crosstalk Widening
    # --------------------------------
    shift = int(sr * 0.0008)  # tiny analog drift
    if shift > 0:
        left = np.roll(analog, shift)
        right = np.roll(analog, -shift)
    else:
        left = analog.copy()
        right = analog.copy()

    stereo = np.stack([left, right], axis=1)

    # Normalize to avoid clipping
    max_val = max(np.max(np.abs(stereo)), 1e-6)
    stereo = (stereo / max_val) * 0.98

    # --------------------------------
    # 7. Warm Analog Limiter
    # --------------------------------
    # soft clip instead of hard limit
    stereo = np.tanh(stereo * 1.2).astype(np.float32)

    # --------------------------------
    # 8. Save mastered file
    # --------------------------------
    out_path = tempfile.mktemp(suffix=".wav")
    sf.write(out_path, stereo, sr)

    with open(out_path, "rb") as f:
        return f.read()


# ------------------------------------------------------------
# PUBLIC DISPATCHER
# ------------------------------------------------------------
def analog_master(audio_url, hq=False):
    """
    Called by app.py
    hq=True → HQ Analog Tape + Tube Mastering
    """
    if isinstance(hq, str) and hq.lower() in ["1", "true", "yes", "y", "hq", "librosa"]:
        hq = True

    if hq:
        return _analog_hq(audio_url)

    return _analog_fast(audio_url)
