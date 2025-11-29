import tempfile
import subprocess
import requests
import numpy as np
import librosa
import soundfile as sf


# -------------------------------------------------
# FAST DOUBLER (FFmpeg)
# -------------------------------------------------
def _doubler_fast(audio_url):
    """
    Fast stereo doubler via FFmpeg.
    """
    input_path = tempfile.mktemp(suffix=".wav")
    out_path = tempfile.mktemp(suffix=".wav")

    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex",
        "[0:a]asplit=2[l][r];"
        "[r]adelay=12|12,asetrate=44100*0.985[detuned];"
        "[l][detuned]amix=inputs=2:weights=1 1[out]",
        "-map", "[out]",
        out_path
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with open(out_path, "rb") as f:
        return f.read()


# -------------------------------------------------
# HIGH QUALITY DOUBLER (Librosa)
# -------------------------------------------------
def _doubler_hq(audio_url):
    """
    HQ doubler:
    - micro-pitch drift
    - stereo harmonic widening
    - breath/aeration enhancement
    - frequency-domain chorus
    """
    input_path = tempfile.mktemp(suffix=".wav")
    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    y, sr = librosa.load(input_path, sr=44100)

    # ---------------------------
    # 1. Create detuned copy
    # ---------------------------
    detune_cents = -15  # very subtle drift
    y_detuned = librosa.effects.pitch_shift(y, sr=sr, n_steps=detune_cents / 100)

    # ---------------------------
    # 2. Chorus via modulated delay
    # ---------------------------
    t = np.linspace(0, len(y) / sr, len(y))
    lfo = 0.002 * np.sin(2 * np.pi * 0.8 * t)  # 0.8 Hz modulation
    chorus = np.zeros_like(y)

    for i in range(len(y)):
        d = int(sr * lfo[i])
        if i - d >= 0:
            chorus[i] = y[i - d]

    # ---------------------------
    # 3. Breath excite layer
    # ---------------------------
    breath = librosa.effects.preemphasis(y)
    breath = librosa.effects.bandpass(breath, sr=sr, low=3000, high=8000)
    if np.max(np.abs(breath)) > 0:
        breath /= np.max(np.abs(breath))

    # ---------------------------
    # 4. Stereo widening layer
    # ---------------------------
    left = y + 0.35 * y_detuned + 0.20 * chorus
    right = y - 0.35 * y_detuned + 0.20 * chorus + 0.15 * breath

    # Normalize
    max_val = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-6)
    left /= max_val
    right /= max_val

    stereo = np.stack([left, right], axis=1)

    # ---------------------------
    # Save WAV
    # ---------------------------
    out_path = tempfile.mktemp(suffix=".wav")
    sf.write(out_path, stereo.astype(np.float32), sr)

    with open(out_path, "rb") as f:
        return f.read()


# -------------------------------------------------
# PUBLIC API ENTRYPOINT
# -------------------------------------------------
def vocal_doubler(audio_url, hq=False):
    """
    Called by app.py
    hq=True → use Librosa HQ doubler
    """
    if isinstance(hq, str) and hq.lower() in ["1", "true", "yes", "y", "librosa", "hq"]:
        hq = True

    if hq:
        return _doubler_hq(audio_url)

    return _doubler_fast(audio_url)
