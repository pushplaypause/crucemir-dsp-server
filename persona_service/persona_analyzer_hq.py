# persona_service/persona_analyzer_hq.py

import numpy as np
import librosa
import soundfile as sf
import tempfile
import pyloudnorm as pyln

def analyze_persona_hq(audio_bytes):
    """
    High-quality but Render-safe persona analyzer.
    Uses librosa + numpy only (no heavy models).
    Returns vocal fingerprint features that your SoVITS engine can use.
    """

    # Save to temp WAV
    tmp = tempfile.mktemp(suffix=".wav")
    with open(tmp, "wb") as f:
        f.write(audio_bytes)

    y, sr = librosa.load(tmp, sr=44100, mono=True)

    # Normalize
    y = librosa.util.normalize(y)

    # -----------------------------
    # 1) Pitch (F0 range)
    # -----------------------------
    f0, _, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C6"),
        sr=sr
    )

    voiced = f0[~np.isnan(f0)]
    if len(voiced) > 0:
        pitch_min = float(np.min(voiced))
        pitch_max = float(np.max(voiced))
        pitch_mean = float(np.mean(voiced))
    else:
        pitch_min = pitch_max = pitch_mean = 0

    # -----------------------------
    # 2) Spectral features
    # -----------------------------
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))

    # -----------------------------
    # 3) Formants (simple LPC)
    # -----------------------------
    try:
        lpc = librosa.lpc(y, order=16)
        formants = lpc.tolist()
    except:
        formants = []

    # -----------------------------
    # 4) Loudness
    # -----------------------------
    meter = pyln.Meter(sr)
    loudness = float(meter.integrated_loudness(y))

    # -----------------------------
    # 5) Energy shape
    # -----------------------------
    energy = librosa.feature.rms(y=y)
    energy_mean = float(np.mean(energy))

    return {
        "pitch_min": pitch_min,
        "pitch_max": pitch_max,
        "pitch_mean": pitch_mean,

        "spectral_centroid": centroid,
        "spectral_bandwidth": bandwidth,
        "spectral_rolloff": rolloff,

        "formants": formants,
        "loudness": loudness,
        "energy": energy_mean
    }
