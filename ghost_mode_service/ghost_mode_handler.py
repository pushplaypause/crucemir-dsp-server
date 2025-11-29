import tempfile
import subprocess
import requests
import numpy as np
import librosa
import soundfile as sf
import scipy.signal as signal


# ------------------------------------------------------------
# FAST MODE (FFmpeg-based)
# ------------------------------------------------------------
def _ghost_fast(audio_url):
    """
    Fast, CPU-safe ghost mode.
    """
    input_path = tempfile.mktemp(suffix=".wav")
    out_path = tempfile.mktemp(suffix=".wav")

    # Download audio
    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    # FFmpeg spectral/temporal ghosting
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af",
        (
            "asetrate=44100*0.9,"
            "atempo=1/0.9,"
            "highpass=f=300,"
            "aecho=0.8:0.9:80:0.7"
        ),
        out_path
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with open(out_path, "rb") as f:
        return f.read()


# ------------------------------------------------------------
# HQ MODE (Librosa DSP-based)
# ------------------------------------------------------------
def _ghost_hq(audio_url):
    """
    HQ cinematic ghost mode using spectral decomposition.
    MUCH heavier DSP but produces a signature 'haunted' sound.
    """
    input_path = tempfile.mktemp(suffix=".wav")

    # Download audio
    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    # Load audio
    y, sr = librosa.load(input_path, sr=44100)

    # ---------------------------------------
    # Breath layer — whisper noise
    # ---------------------------------------
    breath = signal.lfilter([1, -1], [1], y)                # whisper extraction
    breath = librosa.effects.preemphasis(breath)            # high-end crackle
    breath = librosa.effects.bandpass(breath, sr=sr,
                                      low=2000, high=8000)  # isolate breath band

    if np.max(np.abs(breath)) > 0:
        breath /= np.max(np.abs(breath))

    # ---------------------------------------
    # Harmonic layer — ghost warmth
    # ---------------------------------------
    harm = librosa.effects.harmonic(y)
    harm *= 1.3
    if np.max(np.abs(harm)) > 0:
        harm /= np.max(np.abs(harm))

    # ---------------------------------------
    # Pitch ghost — formant-shifted phantom tone
    # ---------------------------------------
    shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=-3)
    shifted = librosa.effects.preemphasis(shifted)
    if np.max(np.abs(shifted)) > 0:
        shifted /= np.max(np.abs(shifted))

    # ---------------------------------------
    # Combine layers
    # ---------------------------------------
    ghost = (
        y * 0.6 +
        breath * 0.35 +
        harm * 0.35 +
        shifted * 0.35
    )

    ghost = ghost / max(1e-6, np.max(np.abs(ghost)))

    # Save WAV
    out_path = tempfile.mktemp(suffix=".wav")
    sf.write(out_path, ghost.astype(np.float32), sr)

    with open(out_path, "rb") as f:
        return f.read()


# ------------------------------------------------------------
# PUBLIC ENTRYPOINT (called by app.py)
# ------------------------------------------------------------
def apply_ghost_mode(audio_url, hq=False):
    """
    Master entrypoint.
    audio_url: URL to WAV/MP3
    hq: bool or string ("1", "true", "hq", etc.)
    """

    # Normalize HQ flag
    if isinstance(hq, str):
        if hq.lower() in ["1", "true", "yes", "y", "hq", "librosa"]:
            hq = True

    if hq:
        return _ghost_hq(audio_url)

    return _ghost_fast(audio_url)
