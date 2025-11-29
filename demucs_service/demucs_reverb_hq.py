import tempfile
import requests
import librosa
import numpy as np
import soundfile as sf
import scipy.signal as signal


def apply_demucs_hq_reverb(audio_url, reverb_amount=0.8):
    """
    HQ Cinematic Reverb and Spatial Enhancement for DEMUCS stems.
    """
    # --------------------------------------------------------
    # Load stem from URL
    # --------------------------------------------------------
    input_path = tempfile.mktemp(suffix=".wav")

    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    y, sr = librosa.load(input_path, sr=44100)
    dry = y.astype(np.float32)

    # Ensure stereo output even for mono stems
    if len(dry.shape) == 1:
        dry = np.stack([dry, dry], axis=1)

    left = dry[:, 0]
    right = dry[:, 1]


    # --------------------------------------------------------
    # 1. Pre-delay (10–20 ms)
    # --------------------------------------------------------
    predelay_samples = int(sr * 0.015)
    left_pre = np.pad(left, (predelay_samples, 0))[:len(left)]
    right_pre = np.pad(right, (predelay_samples, 0))[:len(right)]
    predelayed = np.stack([left_pre, right_pre], axis=1)


    # --------------------------------------------------------
    # 2. Early reflections (4 small allpass filters)
    # --------------------------------------------------------
    def early_reflections(x):
        delays = [0.007, 0.011, 0.017, 0.019]
        gains = [0.22, 0.18, 0.14, 0.10]
        out = x.copy()
        for d, g in zip(delays, gains):
            samples = int(sr * d)
            out += np.pad(x * g, (samples, 0))[:len(x)]
        return out

    er_left = early_reflections(left)
    er_right = early_reflections(right)
    early = np.stack([er_left, er_right], axis=1)


    # --------------------------------------------------------
    # 3. Reverb tail convolution with custom impulses
    # --------------------------------------------------------
    tail_impulse = signal.exponential(M=int(sr * 1.5), tau=sr * 0.55, sym=False)
    tail_left = signal.fftconvolve(left, tail_impulse, mode='same')
    tail_right = signal.fftconvolve(right, tail_impulse, mode='same')
    tail = np.stack([tail_left, tail_right], axis=1)


    # --------------------------------------------------------
    # 4. High-frequency shimmer boost (10–14 kHz)
    # --------------------------------------------------------
    shimmer = librosa.effects.bandpass(left, sr=sr, low=9000, high=14000)
    shimmer = shimmer / max(1e-6, np.max(np.abs(shimmer))) * 0.25

    shimmer_st = np.stack([shimmer, shimmer], axis=1)


    # --------------------------------------------------------
    # 5. Spatial widening via mid/side processing
    # --------------------------------------------------------
    mid = (early[:, 0] + early[:, 1]) * 0.5
    side = (early[:, 0] - early[:, 1]) * 0.5 * 1.4  # widen

    widened = np.stack([mid + side, mid - side], axis=1)


    # --------------------------------------------------------
    # 6. Glue compression (gentle)
    # --------------------------------------------------------
    def soft_knee(x, thresh=0.6, ratio=3):
        above = np.abs(x) > thresh
        x[above] = thresh + (x[above] - thresh) / ratio
        return x

    widened = soft_knee(widened.copy(), thresh=0.55, ratio=3.5)


    # --------------------------------------------------------
    # 7. Combine All Layers
    # --------------------------------------------------------
    wet = (
        predelayed * 0.35 +
        early * 0.25 +
        tail * reverb_amount +
        shimmer_st * 0.20 +
        widened * 0.40
    )

    mix = dry * (1 - reverb_amount * 0.5) + wet

    # Normalize
    mix /= max(1e-6, np.max(np.abs(mix))) * 1.01


    # --------------------------------------------------------
    # 8. Save output file
    # --------------------------------------------------------
    out_path = tempfile.mktemp(suffix=".wav")
    sf.write(out_path, mix.astype(np.float32), sr)

    with open(out_path, "rb") as f:
        return f.read()
