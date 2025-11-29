import numpy as np
import librosa
import requests
import tempfile
import scipy.signal as signal
import pyloudnorm as pyln


def analyze_persona_hq(audio_bytes):
    tmp = tempfile.mktemp(suffix=".wav")
    with open(tmp, "wb") as f:
        f.write(audio_bytes)

    y, sr = librosa.load(tmp, sr=44100)
    y = y.astype(np.float32)

    features = {}

    # -----------------------------
    # Timbre Curve
    # -----------------------------
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features["timbre_brightness"] = float(np.mean(centroid))
    features["timbre_variation"] = float(np.std(centroid))

    # -----------------------------
    # Pitch stats
    # -----------------------------
    f0, voiced = librosa.pyin(
        y,
        fmin=70,
        fmax=600,
        sr=sr
    )
    f0_clean = f0[~np.isnan(f0)]
    if len(f0_clean) > 0:
        features["pitch_min"] = float(np.min(f0_clean))
        features["pitch_max"] = float(np.max(f0_clean))
        features["pitch_median"] = float(np.median(f0_clean))
    else:
        features["pitch_min"] = 0
        features["pitch_max"] = 0
        features["pitch_median"] = 0

    # -----------------------------
    # Vibrato
    # -----------------------------
    if len(f0_clean) > 30:
        diff = np.diff(f0_clean)
        vib_rate = np.mean(np.abs(np.fft.rfft(diff)))
        vib_depth = np.std(diff)
        features["vibrato_rate"] = float(vib_rate)
        features["vibrato_depth"] = float(vib_depth)
    else:
        features["vibrato_rate"] = 0
        features["vibrato_depth"] = 0

    # -----------------------------
    # Breathiness
    # -----------------------------
    breath = signal.lfilter([1, -1], [1], y)
    features["breathiness"] = float(np.mean(np.abs(breath)))

    # -----------------------------
    # Formants (F1, F2, F3)
    # -----------------------------
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    formants = []
    for _ in range(3):
        idx = np.argmax(S.mean(axis=1))
        formants.append(float(freqs[idx]))
        S[idx] = 0
    features["formants"] = formants

    # -----------------------------
    # Loudness (LUFS)
    # -----------------------------
    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(y)
    features["loudness"] = float(loudness)

    # -----------------------------
    # Emotional Tone Heuristic
    # (simple + stable)
    # -----------------------------
    if features["breathiness"] > 0.1:
        features["emotion"] = "intimate / breathy"
    elif features["timbre_brightness"] > 3000:
        features["emotion"] = "bright / energetic"
    else:
        features["emotion"] = "neutral / calm"

    return features
