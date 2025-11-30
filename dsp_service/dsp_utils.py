import numpy as np
import librosa
import scipy.signal as signal


# -------------------------------------------------------
# 1. ONSET DETECTION (replaces julius onset detection)
# -------------------------------------------------------
def detect_onsets(audio, sr, backtrack=True):
    """
    Returns a list of onsets (in seconds) using high-accuracy librosa methods.
    """
    o_env = librosa.onset.onset_strength(y=audio, sr=sr)
    onsets = librosa.onset.onset_detect(onset_envelope=o_env, sr=sr, backtrack=backtrack)
    return librosa.frames_to_time(onsets, sr=sr)


# -------------------------------------------------------
# 2. TEMPO ESTIMATION (replaces julius tempo)
# -------------------------------------------------------
def estimate_tempo(audio, sr):
    """
    Returns tempo (BPM) and full beat positions.
    """
    tempo, beats = librosa.beat.beat_track(y=audio, sr=sr, units="time")
    return float(tempo), beats.tolist()


# -------------------------------------------------------
# 3. ENERGY MAP (replaces julius energy)
# -------------------------------------------------------
def compute_energy_map(audio, sr, window=2048, hop=512):
    """
    Returns per-frame RMS energy curve.
    """
    rms = librosa.feature.rms(y=audio, frame_length=window, hop_length=hop)[0]
    times = librosa.frames_to_time(range(len(rms)), sr=sr)
    return [{"time": float(t), "energy": float(e)} for t, e in zip(times, rms)]


# -------------------------------------------------------
# 4. SILENCE DETECTION (replaces julius silence / trimming)
# -------------------------------------------------------
def detect_silence(audio, sr, threshold=0.015, min_silence_ms=300):
    """
    Returns segments of speech/music vs silence.
    """
    frame_length = int(sr * (min_silence_ms / 1000))
    hop = frame_length // 2
    rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop)[0]
    silence_frames = np.where(rms < threshold)[0]
    times = librosa.frames_to_time(silence_frames, sr=sr)
    return times.tolist()


# -------------------------------------------------------
# 5. SLICE AUDIO ON ONSETS (replaces julius slicing)
# -------------------------------------------------------
def slice_by_onsets(audio, sr):
    """
    Returns audio slices automatically divided by onset detection.
    """
    slices = []
    onsets = detect_onsets(audio, sr)
    onsets = [0.0] + list(onsets) + [len(audio)/sr]

    for i in range(len(onsets)-1):
        start = int(onsets[i] * sr)
        end = int(onsets[i+1] * sr)
        segment = audio[start:end]
        slices.append({
            "start": float(onsets[i]),
            "end": float(onsets[i+1]),
            "samples": segment
        })

    return slices


# -------------------------------------------------------
# 6. TRANSIENT DETECTION (modern replacement)
# -------------------------------------------------------
def detect_transients(audio, sr):
    """
    High-accuracy transient detection using spectral flux.
    """
    S = np.abs(librosa.stft(audio))
    flux = librosa.onset.onset_strength(S=librosa.power_to_db(S))
    peaks = librosa.util.peak_pick(flux, 3, 3, 3, 5, 0.5, 5)
    times = librosa.frames_to_time(peaks, sr=sr)
    return times.tolist()
