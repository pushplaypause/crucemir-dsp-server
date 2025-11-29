import librosa
import soundfile as sf
import tempfile
import numpy as np
import scipy.signal as signal
import requests
import os


def ghost_mode_hq(audio_url):
    """
    High-quality Ghost Mode using librosa DSP.
    Much heavier CPU cost but beautiful spectral ghosting.
    """

    # --------------------------
    # Download into temp file
    # --------------------------
    input_path = tempfile.mktemp(suffix=".wav")
    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    # --------------------------
    # Load audio
    # --------------------------
    y, sr = librosa.load(input_path, sr=44100)

    # --------------------------
    # Breath layer (whisper)
    # --------------------------
    # Pre-emphasis + high-frequency focus
    breath = signal.lfilter([1, -1], [1], y)
    breath = librosa.effects.preemphasis(breath)

    # Slight bandpass to isolate breathiness
    breath = librosa.effects.bandpass(breath, sr=sr, low=2000, high=8000)

    # Normalize breath layer
    if np.max(np.abs(breath)) > 0:
        breath /= np.max(np.abs(breath))

    # --------------------------
    # Harmonic enhancement
    # --------------------------
    harm = librosa.effects.harmonic(y)
    harm *= 1.4
    if np.max(np.abs(harm)) > 0:
        harm /= np.max(np.abs(harm))

    # --------------------------
    # Formant-shifted spectral ghost
    # --------------------------
    pitch_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=-3)
    pitch_shifted = librosa.effects.preemphasis(pitch_shifted)

    if np.max(np.abs(pitch_shifted)) > 0:
        pitch_shifted /= np.max(np.abs(pitch_shifted))

    # --------------------------
    # Combine layers
    # --------------------------
    ghost = (
        y * 0.5 +
        breath * 0.35 +
        harm * 0.4 +
        pitch_shifted * 0.25
    )

    ghost /= max(1e-8, np.max(np.abs(ghost)))

    # --------------------------
    # Save to temp file
    # --------------------------
    out_path = tempfile.mktemp(suffix=".wav")
    sf.write(out_path, ghost.astype(np.float32), sr)

    # --------------------------
    # Return raw bytes
    # --------------------------
    with open(out_path, "rb") as f:
        return f.read()
