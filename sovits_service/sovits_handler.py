import tempfile
import numpy as np
import librosa
import soundfile as sf
import scipy.signal as signal


# -----------------------------------------------------------
# Utility: create a REAL bandpass filter (HQ)
# -----------------------------------------------------------
def bandpass_filter(y, sr, low, high, gain=1.0, order=6):
    """
    HQ bandpass filter using scipy SOS filter.
    """
    sos = signal.butter(
        order,
        [low / (sr / 2), high / (sr / 2)],
        btype="bandpass",
        output="sos"
    )
    return gain * signal.sosfilt(sos, y)


# -----------------------------------------------------------
# High-end SoVITS Enhancer
# -----------------------------------------------------------
def enhance_sovits(audio_bytes):
    """
    HQ enhancement chain for SoVITS output.
    Input: raw WAV bytes
    Output: enhanced stereo WAV bytes
    """

    # ---------------------------------------------
    # Load from bytes → float32 mono array
    # ---------------------------------------------
    in_path = tempfile.mktemp(suffix=".wav")
    with open(in_path, "wb") as f:
        f.write(audio_bytes)

    y, sr = librosa.load(in_path, sr=44100, mono=True)
    y = y.astype(np.float32)

    # ---------------------------------------------
    # 1. De-mud (remove 300–600 Hz mud)
    # ---------------------------------------------
    mud = bandpass_filter(y, sr, 300, 600, gain=1.0)
    cleaned = y - mud * 0.45

    # ---------------------------------------------
    # 2. Presence boost (2.5–4.5 kHz)
    # ---------------------------------------------
    presence = bandpass_filter(y, sr, 2500, 4500, gain=0.35)
    cleaned += presence

    # ---------------------------------------------
    # 3. Air boost (8–12 kHz)
    # ---------------------------------------------
    air = bandpass_filter(y, sr, 8000, 12000, gain=0.50)
    cleaned += air

    # ---------------------------------------------
    # 4. Tube harmonics (soft saturation)
    # ---------------------------------------------
    saturated = cleaned + 0.12 * (cleaned ** 3)
    saturated = saturated / (np.max(np.abs(saturated)) + 1e-6)

    # ---------------------------------------------
    # 5. De-esser (5–8 kHz subtractive)
    # ---------------------------------------------
    sib = bandpass_filter(saturated, sr, 5000, 8000, gain=1.0)
    deessed = saturated - sib * 0.22

    # ---------------------------------------------
    # 6. Stereo widening (drift-based)
    # ---------------------------------------------
    shift = int(sr * 0.00065)   # 0.65 ms shift
    left = np.roll(deessed, shift)
    right = np.roll(deessed, -shift)
    stereo = np.stack([left, right], axis=1)

    # Normalize before limiting
    max_amp = np.max(np.abs(stereo)) + 1e-6
    stereo = stereo / max_amp * 0.95

    # ---------------------------------------------
    # 7. Soft limiter
    # ---------------------------------------------
    stereo = np.tanh(stereo * 1.2).astype(np.float32)

    # ---------------------------------------------
    # 8. Save output file
    # ---------------------------------------------
    out_path = tempfile.mktemp(suffix=".wav")
    sf.write(out_path, stereo, sr)

    return open(out_path, "rb").read()
