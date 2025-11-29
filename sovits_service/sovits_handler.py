import tempfile
import requests
import numpy as np
import librosa
import soundfile as sf
import scipy.signal as signal


def enhance_sovits(audio_bytes):
    """
    HQ post-processing chain for SoVITS output.
    Input: raw WAV bytes
    Output: enhanced WAV bytes
    """

    # ----------------------------------------------------
    # Load from bytes → temp WAV
    # ----------------------------------------------------
    in_path = tempfile.mktemp(suffix=".wav")
    with open(in_path, "wb") as f:
        f.write(audio_bytes)

    y, sr = librosa.load(in_path, sr=44100)
    y = y.astype(np.float32)


    # ----------------------------------------------------
    # 1. De-mud (cut 300–600 Hz)
    # ----------------------------------------------------
    mud = librosa.effects.bandpass(y, sr=sr, low=300, high=600)
    cleaned = y - mud * 0.45


    # ----------------------------------------------------
    # 2. Presence Boost (2.5–4.5 kHz)
    # ----------------------------------------------------
    presence = librosa.effects.bandpass(y, sr=sr, low=2500, high=4500)
    cleaned += presence * 0.35


    # ----------------------------------------------------
    # 3. Air Boost (8–12 kHz)
    # ----------------------------------------------------
    air = librosa.effects.bandpass(y, sr=sr, low=8000, high=12000)
    cleaned += air * 0.50


    # ----------------------------------------------------
    # 4. Tube Harmonics (soft saturation)
    # ----------------------------------------------------
    saturated = cleaned + 0.12 * (cleaned ** 3)
    saturated = saturated / max(1e-6, np.max(np.abs(saturated)))


    # ----------------------------------------------------
    # 5. De-Esser (sibilance reduction)
    # ----------------------------------------------------
    sibilance = librosa.effects.bandpass(y, sr=sr, low=5000, high=8000)
    deessed = saturated - sibilance * 0.25


    # ----------------------------------------------------
    # 6. Stereo Widening (analog drift)
    # ----------------------------------------------------
    shift = int(sr * 0.0006)
    left = np.roll(deessed, shift)
    right = np.roll(deessed, -shift)

    stereo = np.stack([left, right], axis=1)

    # Normalize before limiter
    max_amp = max(1e-6, np.max(np.abs(stereo)))
    stereo = stereo / max_amp * 0.95


    # ----------------------------------------------------
    # 7. Soft Limiter
    # ----------------------------------------------------
    stereo = np.tanh(stereo * 1.2).astype(np.float32)


    # ----------------------------------------------------
    # 8. Save to temp output file
    # ----------------------------------------------------
    out_path = tempfile.mktemp(suffix=".wav")
    sf.write(out_path, stereo, sr)

    with open(out_path, "rb") as f:
        return f.read()
