import tempfile
import requests
import numpy as np
import soundfile as sf
import librosa
import scipy.signal as signal
import pyloudnorm as pyln


# ------------------------------------------------------------
# HQ INSTRUMENTAL MASTER
# ------------------------------------------------------------
def master_instrumental_hq(audio_url):
    """
    High-quality mastering pipeline for MusicGen instrumentals.
    """

    # --------------------------------------------------------
    # 1. Download + Load Audio
    # --------------------------------------------------------
    tmp = tempfile.mktemp(suffix=".wav")
    with open(tmp, "wb") as f:
        f.write(requests.get(audio_url).content)

    y, sr = librosa.load(tmp, sr=44100)
    y = y.astype(np.float32)


    # --------------------------------------------------------
    # 2. Spectral Tilt (MusicGen Fix)
    # --------------------------------------------------------
    # Reduce low-mid mud (200–500 Hz)
    mud = librosa.effects.bandpass(y, sr=sr, low=200, high=500) * 0.55

    # Boost presence (2–4 kHz)
    presence = librosa.effects.bandpass(y, sr=sr, low=2500, high=4500) * 1.35

    # Boost air (10–14k)
    air = librosa.effects.bandpass(y, sr=sr, low=10000, high=14000) * 1.45

    tilt = (
        y * 0.75 +
        presence * 0.15 +
        air * 0.25 -
        mud * 0.25
    )


    # --------------------------------------------------------
    # 3. Transient Punch Enhancement
    # --------------------------------------------------------
    # Simple transient shaper (difference filter)
    transients = tilt - signal.lfilter([1], [1, -0.85], tilt)
    punch = tilt + transients * 0.45


    # --------------------------------------------------------
    # 4. Tube + Tape Saturation
    # --------------------------------------------------------
    tube = punch + 0.15 * (punch ** 3)
    tape = np.tanh(tube * 1.6) * 0.7 + tube * 0.3

    # Combine analog saturation layers
    analog = (punch * 0.6 + tape * 0.4)
    analog = analog / max(1e-6, np.max(np.abs(analog)))


    # --------------------------------------------------------
    # 5. SSL Bus Glue Compression
    # --------------------------------------------------------
    def ssl_glue(x, thresh=0.5, ratio=4):
        above = np.abs(x) > thresh
        x[above] = thresh + (np.abs(x) - thresh) / ratio
        return x * np.sign(x)

    glued = ssl_glue(analog.copy(), thresh=0.52, ratio=3.5)


    # --------------------------------------------------------
    # 6. Mid/Side Enhancement (Cinematic Width)
    # --------------------------------------------------------
    # Convert to stereo if mono
    if glued.ndim == 1:
        left = glued
        right = glued.copy()
    else:
        left, right = glued[:, 0], glued[:, 1]

    mid = (left + right) * 0.5
    side = (left - right) * 0.5 * 1.25  # widen 25%

    stereo = np.stack([mid + side, mid - side], axis=1)


    # --------------------------------------------------------
    # 7. Soft Limiter + LUFS Normalization
    # --------------------------------------------------------
    meter = pyln.Meter(sr)
    loud = meter.integrated_loudness(stereo.mean(axis=1))

    target_lufs = -11.0  # modern instrumental loudness target
    loud_norm = pyln.normalize.loudness(stereo, loud, target_lufs)

    # Final soft clip
    limited = np.tanh(loud_norm * 1.3).astype(np.float32)


    # --------------------------------------------------------
    # 8. Save to output
    # --------------------------------------------------------
    out_path = tempfile.mktemp(suffix=".wav")
    sf.write(out_path, limited, sr)

    with open(out_path, "rb") as f:
        return f.read()
