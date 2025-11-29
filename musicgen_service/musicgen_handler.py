import tempfile
import requests
import numpy as np
import soundfile as sf
from instrumental_master_service.instrumental_master_hq import master_instrumental_hq
from musicgen_service.musicgen_handler import generate_music  # your existing


def enhance_musicgen(audio_bytes):
    """HQ cleanup pass."""
    tmp = tempfile.mktemp(suffix=".wav")
    with open(tmp, "wb") as f:
        f.write(audio_bytes)

    y, sr = sf.read(tmp)
    y = y.astype(np.float32)

    # spectral tilt
    import librosa
    lowmid = librosa.effects.bandpass(y, sr=sr, low=200, high=600) * 0.65
    presence = librosa.effects.bandpass(y, sr=sr, low=2500, high=5000) * 1.3
    air = librosa.effects.bandpass(y, sr=sr, low=10000, high=14000) * 1.4

    cleaned = (
        y * 0.8
        + presence * 0.25
        + air * 0.20
        - lowmid * 0.25
    )

    cleaned /= max(1e-6, np.max(np.abs(cleaned)))

    out_tmp = tempfile.mktemp(suffix=".wav")
    sf.write(out_tmp, cleaned, sr)

    with open(out_tmp, "rb") as f:
        return f.read()


def musicgen_hq(prompt, duration=32, bpm=None, seed=None):
    """
    Full 3-Pass HQ MusicGen pipeline.
    """
    # ------------------------------
    # PASS 1: generation
    # ------------------------------
    generated = generate_music(prompt, duration, bpm, seed)

    if isinstance(generated, dict) and "audio_bytes" in generated:
        audio_bytes = generated["audio_bytes"]
    else:
        audio_bytes = generated  # fallback

    # ------------------------------
    # PASS 2: spectral enhancement
    # ------------------------------
    enhanced = enhance_musicgen(audio_bytes)

    # ------------------------------
    # PASS 3: HQ Instrumental Mastering
    # ------------------------------
    tmp_path = tempfile.mktemp(suffix=".wav")
    with open(tmp_path, "wb") as f:
        f.write(enhanced)

    mastered = master_instrumental_hq(tmp_path)

    return mastered
