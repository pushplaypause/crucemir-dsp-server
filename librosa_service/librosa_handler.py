import librosa
import numpy as np
import tempfile
import os
from scipy.stats import zscore
from pydub import AudioSegment
import crepe
import scipy

def load_audio(file_path, sr=44100):
    """Load audio using librosa."""
    y, sr = librosa.load(file_path, sr=sr, mono=True)
    return y, sr

def compute_bpm(y, sr):
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    return float(tempo)

def compute_key(y, sr):
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)

    major_template = np.array([1,0,1,0,1,1,0,1,0,1,0,1])
    minor_template = np.array([1,0,1,1,0,1,0,1,1,0,1,0])

    correlation_major = np.correlate(chroma_mean, major_template)
    correlation_minor = np.correlate(chroma_mean, minor_template)

    key_index = np.argmax(chroma_mean)

    keys = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

    if correlation_major > correlation_minor:
        return f"{keys[key_index]} Major"
    else:
        return f"{keys[key_index]} Minor"

def compute_energy(y):
    rms = np.sqrt(np.mean(y ** 2))
    return float(min(100, max(0, rms * 5000)))

def compute_pitch(y, sr):
    _, frequency, confidence, _ = crepe.predict(y, sr, step_size=100)
    if len(confidence) == 0:
        return None, None

    best_idx = np.argmax(confidence)
    return float(frequency[best_idx]), float(confidence[best_idx])

def compute_duration(file_path):
    audio = AudioSegment.from_file(file_path)
    return audio.duration_seconds

def analyze_audio_with_librosa(input_path):
    y, sr = load_audio(input_path)

    bpm = compute_bpm(y, sr)
    key = compute_key(y, sr)
    energy = compute_energy(y)
    pitch, pitch_conf = compute_pitch(y, sr)
    duration = compute_duration(input_path)

    return {
        "bpm": bpm,
        "key": key,
        "energy": energy,
        "pitch_hz": pitch,
        "pitch_confidence": pitch_conf,
        "duration_seconds": duration
    }
