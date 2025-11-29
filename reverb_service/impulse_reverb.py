import numpy as np
import soundfile as sf
import scipy.signal as signal
import os

# -------------------------------------------------------------
# STATIC IR LOAD (cached in memory after first import)
# -------------------------------------------------------------
IR_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "impulse_responses",
    "cinematic_tail.wav"
)

_cached_ir = None
_cached_ir_sr = None


def _load_ir():
    """Loads IR once, caches it for later calls."""
    global _cached_ir, _cached_ir_sr

    if _cached_ir is not None:
        return _cached_ir, _cached_ir_sr

    ir, sr = sf.read(IR_PATH)

    # Convert stereo IR → mono (more consistent convolution)
    if ir.ndim > 1:
        ir = ir.mean(axis=1)

    # Normalize IR to prevent insane reverb bursts
    ir = ir / (np.max(np.abs(ir)) + 1e-6)

    _cached_ir = ir.astype(np.float32)
    _cached_ir_sr = sr
    return _cached_ir, _cached_ir_sr


# -------------------------------------------------------------
# EQ helper for IR shaping
# -------------------------------------------------------------
def _eq_ir(ir, sr, low_shelf=0.1, high_shelf=0.15):
    """
    Very light IR EQ shaping:
    low_shelf adds warmth,
    high_shelf boosts air.
    """
    # Simple FFT domain EQ (low cost)
    fft = np.fft.rfft(ir)

    freqs = np.fft.rfftfreq(len(ir), d=1/sr)

    # Warm low shelf (below 300 Hz)
    fft[freqs < 300] *= (1.0 + low_shelf)

    # Air shelf (above 6 kHz)
    fft[freqs > 6000] *= (1.0 + high_shelf)

    return np.fft.irfft(fft).astype(np.float32)


# -------------------------------------------------------------
# Main Convolution Reverb
# -------------------------------------------------------------
def apply_convolution_reverb(audio, sr, mix=0.28, dampen=0.15):
    """
    HQ cinematic convolution reverb with:
    - IR caching
    - IR resampling
    - IR EQ shaping
    - dampened high-frequency decay
    - safe normalization

    mix:    amount of reverb (0–1)
    dampen: exponential decay factor for tail brightness
    """

    # ---------------------------------------------------------
    # LOAD IR
    # ---------------------------------------------------------
    ir, ir_sr = _load_ir()

    # ---------------------------------------------------------
    # Resample IR to match the audio sample rate
    # ---------------------------------------------------------
    if ir_sr != sr:
        ir = signal.resample_poly(ir, sr, ir_sr)

    # ---------------------------------------------------------
    # Apply IR EQ shaping (film-style)
    # ---------------------------------------------------------
    ir = _eq_ir(ir, sr)

    # ---------------------------------------------------------
    # Apply dampening to IR (gentle HF decay)
    # ---------------------------------------------------------
    n = np.linspace(0, 1, len(ir))
    ir = ir * np.exp(-dampen * n)

    # ---------------------------------------------------------
    # Fast convolution (FFT-based)
    # ---------------------------------------------------------
    # Use rfft/irfft for CPU efficiency
    wet = signal.fftconvolve(audio, ir, mode="full")
    wet = wet[:len(audio)]

    # ---------------------------------------------------------
    # Normalize wet tail BEFORE mixing
    # ---------------------------------------------------------
    wet = wet / (np.max(np.abs(wet)) + 1e-6)

    # ---------------------------------------------------------
    # Mix dry + wet
    # ---------------------------------------------------------
    out = (1 - mix) * audio + (mix * wet)

    # ---------------------------------------------------------
    # Global normalization with soft limiting
    # ---------------------------------------------------------
    max_amp = np.max(np.abs(out)) + 1e-6
    out = out / max_amp

    # Very soft clip smoothing (avoids digital harshness)
    out = np.tanh(out * 1.15).astype(np.float32)

    return out
