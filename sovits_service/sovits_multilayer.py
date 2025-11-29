import uuid
import subprocess
import tempfile
import os
import base64
import json
import numpy as np
import soundfile as sf
from sovits_service.sovits_handler import extract_sovits_features

# Mapping internal vocal mode -> CLI code
BASE_MODE_CODES = {
    "neutral": "0",
    "whisper": "1",
    "ghost": "2",
    "aggressive": "3"
}

# DSP-only expansions
DSP_MODES = [
    "clean", "raspy", "fry", "airy", "warm", "bright", "dark", "metallic",
    "hollow", "cinematic", "breathy", "tense", "relaxed",
    "formant_shift_up", "formant_shift_down",
    "vocoder", "shimmer", "chorus", "double",
    "octave_up", "octave_down",
    "breath_noise", "grit", "distortion", "overdrive",
    "reverb_large", "reverb_small", "reverb_medium",
    "echo", "shadow_layer", "spectral_pad", "harmonic_bloom",
    "fry_scream", "false_cord_scream", "guttural",
    "ghost_soft", "ghost_mid", "ghost_hollow", "ghost_whisper",
    "whisper_soft", "whisper_air", "whisper_breathy"
]

def apply_dsp(y, sr, mode):
    """Applies DSP transformations for non-SoVITS-native modes."""
    import librosa
    import scipy.signal as signal

    if mode == "raspy":
        y = y + 0.03 * np.random.randn(len(y))

    if mode == "fry":
        y = librosa.effects.harmonic(y) * 0.8

    if mode == "airy":
        y = y * 0.7 + librosa.effects.preemphasis(y) * 0.3

    if mode == "breathy":
        noise = np.random.randn(len(y)) * 0.02
        y = y + noise

    if mode == "formant_shift_up":
        y = librosa.effects.pitch_shift(y, sr, n_steps=3)

    if mode == "formant_shift_down":
        y = librosa.effects.pitch_shift(y, sr, n_steps=-3)

    if mode == "chorus":
        delayed = np.pad(y, (200, 0))[:len(y)]
        y = (y + delayed) / 2

    if mode == "double":
        shifted = librosa.effects.pitch_shift(y, sr, n_steps=0.1)
        y = (y + shifted) / 2

    if mode == "octave_up":
        y = librosa.effects.pitch_shift(y, sr, n_steps=12)

    if mode == "octave_down":
        y = librosa.effects.pitch_shift(y, sr, n_steps=-12)

    if mode == "harmonic_bloom":
        harm = librosa.effects.harmonic(y)
        y = (y + harm * 0.4)

    if mode.startswith("reverb"):
        y = np.convolve(y, np.ones(2000)/2000, mode="same")

    if mode == "echo":
        echo = np.pad(y, (4000,0))[:len(y)] * 0.4
        y = y + echo

    return y


def render_sovits_layer(lyrics, midi_data, persona, vocal_mode):
    """Render one SoVITS vocal layer."""
    tmp_l = f"/tmp/lyrics_{uuid.uuid4()}.txt"
    tmp_m = f"/tmp/midi_{uuid.uuid4()}.mid"
    out_wav = f"/tmp/sovits_{uuid.uuid4()}.wav"

    with open(tmp_l, "w") as f: f.write(lyrics)
    with open(tmp_m, "wb") as f: f.write(midi_data)

    mode_code = BASE_MODE_CODES.get(vocal_mode, "0")

    cmd = [
        "sovits-cli", "sing",
        "--lyrics", tmp_l,
        "--midi", tmp_m,
        "--features", persona["features_path"],
        "--vocal-mode", mode_code,
        "--output", out_wav
    ]

    subprocess.run(cmd, check=True)

    audio, sr = sf.read(out_wav, dtype="float32")
    return audio, sr


def run_sovits_multilayer(lyrics, midi_data, persona, layers: dict):
    """Multi-layer SoVITS + DSP rendering engine."""
    final_mix = None
    final_sr = 44100

    for mode, weight in layers.items():
        if weight <= 0:
            continue

        # SoVITS-native mode OR DSP mode?
        if mode in BASE_MODE_CODES:
            audio, sr = render_sovits_layer(lyrics, midi_data, persona, mode)
        else:
            # Base layer then DSP
            audio, sr = render_sovits_layer(lyrics, midi_data, persona, "neutral")
            audio = apply_dsp(audio, sr, mode)

        # Apply weight
        audio = audio * weight

        # Mix
        if final_mix is None:
            final_mix = audio
            final_sr = sr
        else:
            final_mix = final_mix + audio

    # Normalize
    final_mix = final_mix / np.max(np.abs(final_mix))

    out = f"/tmp/final_multilayer_{uuid.uuid4()}.wav"
    sf.write(out, final_mix, final_sr)

    return open(out, "rb").read()
