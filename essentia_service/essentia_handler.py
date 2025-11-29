import librosa
import numpy as np
import tempfile
import subprocess
import os

def run_essentia(audio_path):
    # Convert audio to mono 44.1kHz WAV for stable analysis
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

    subprocess.run([
        "ffmpeg", "-y",
        "-i", audio_path,
        "-ac", "1",
        "-ar", "44100",
        tmp_wav
    ], check=True)

    # Load audio
    y, sr = librosa.load(tmp_wav, sr=44100)

    # BPM (beat tracking)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    # Key estimation (simple chroma-based)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_index = chroma.mean(axis=1).argmax()

    KEYS = [
        "C","C#","D","D#","E","F","F#","G","G#","A","A#","B"
    ]
    key = KEYS[key_index]

    # Scale detection (VERY rough — major/minor)
    if "C#" in key or "F#" in key or "G#" in key:
        scale = "minor"
    else:
        scale = "major"

    # Energy estimation
    energy = float(np.mean(y ** 2))

    return {
        "bpm": float(tempo),
        "key": key,
        "scale": scale,
        "energy": energy
    }
