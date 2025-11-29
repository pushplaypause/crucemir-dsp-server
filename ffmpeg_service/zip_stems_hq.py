import os
import zipfile
import tempfile
import numpy as np
import librosa
import soundfile as sf
import requests


def _download_stem(url, sr=44100):
    """Download a stem URL and load as float32 mono or stereo."""
    tmp = tempfile.mktemp(suffix=".wav")
    with open(tmp, "wb") as f:
        f.write(requests.get(url).content)

    y, stem_sr = librosa.load(tmp, sr=sr, mono=False)

    # Ensure shape (samples, channels)
    if y.ndim == 1:
        y = np.stack([y, y], axis=1)
    else:
        y = y.T  # librosa loads as (channels, samples)

    return y.astype(np.float32), sr


def _loudness_normalize(stem):
    """Normalize per-stem loudness safely."""
    peak = np.max(np.abs(stem))
    if peak > 1e-6:
        stem = stem / peak * 0.95
    return stem


def _fade_edges(stem, sr):
    """Apply tiny fade-in/out to avoid clicks."""
    fade_samples = int(sr * 0.01)  # 10ms fade

    fade_in = np.linspace(0, 1, fade_samples)[None].T
    fade_out = np.linspace(1, 0, fade_samples)[None].T

    stem[:fade_samples] *= fade_in
    stem[-fade_samples:] *= fade_out
    return stem


def _pad_to_length(stem, length):
    """Pad stems to longest duration."""
    if stem.shape[0] >= length:
        return stem
    pad = length - stem.shape[0]
    return np.pad(stem, ((0, pad), (0, 0)), mode='constant')


def create_hq_zip_stems(stem_list):
    """
    stem_list = [
        {"name": "vocals", "url": "..."},
        {"name": "drums", "url": "..."},
        ...
    ]

    Returns: raw bytes of a ZIP file
    """

    # --------------------------------------------------------
    # 1. Download & preprocess stems
    # --------------------------------------------------------
    processed = {}
    max_length = 0

    for stem in stem_list:
        name = stem["name"]
        url = stem["url"]

        audio, sr = _download_stem(url)

        # Loudness normalize
        audio = _loudness_normalize(audio)

        # Fade in/out
        audio = _fade_edges(audio, sr)

        processed[name] = audio
        max_length = max(max_length, audio.shape[0])


    # --------------------------------------------------------
    # 2. Time align & pad all stems
    # --------------------------------------------------------
    for name in processed:
        processed[name] = _pad_to_length(processed[name], max_length)


    # --------------------------------------------------------
    # 3. Create output ZIP
    # --------------------------------------------------------
    zip_path = tempfile.mktemp(suffix=".zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, audio in processed.items():
            out_wav = tempfile.mktemp(suffix=".wav")
            sf.write(out_wav, audio, sr, subtype="FLOAT")  # 32-bit

            # Clean naming
            safe_name = name.replace(" ", "_").lower()
            zf.write(out_wav, f"{safe_name}.wav")


    # --------------------------------------------------------
    # 4. Return ZIP bytes
    # --------------------------------------------------------
    with open(zip_path, "rb") as f:
        return f.read()
