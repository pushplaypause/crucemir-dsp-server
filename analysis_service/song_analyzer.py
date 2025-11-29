import numpy as np
import librosa
import scipy.signal as signal

from chorus_service.chorus_detector import detect_chorus_sections


def analyze_song(audio_path):
    """
    Full song analysis including:
    - BPM
    - Key/Scale
    - Section detection (verse/chorus/outro)
    - Energy map
    - Dynamic range
    """

    # ---------------------------------------------------------
    # LOAD AUDIO
    # ---------------------------------------------------------
    y, sr = librosa.load(audio_path, sr=44100, mono=True)
    total_duration = librosa.get_duration(y=y, sr=sr)

    # ---------------------------------------------------------
    # TEMPO / BPM
    # ---------------------------------------------------------
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(tempo)

    # ---------------------------------------------------------
    # KEY DETECTION (using chroma → Krumhansl-Schmuckler profile)
    # ---------------------------------------------------------
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)

    # Key templates (major + minor)
    maj_profile = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
    min_profile = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])

    major_corr = np.array([np.corrcoef(chroma_mean, np.roll(maj_profile, i))[0,1] for i in range(12)])
    minor_corr = np.array([np.corrcoef(chroma_mean, np.roll(min_profile, i))[0,1] for i in range(12)])

    major_key = np.argmax(major_corr)
    minor_key = np.argmax(minor_corr)

    if major_corr.max() >= minor_corr.max():
        key = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"][major_key]
        scale = "major"
    else:
        key = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"][minor_key]
        scale = "minor"

    # ---------------------------------------------------------
    # ENERGY MAP (per 0.25s)
    # ---------------------------------------------------------
    frame_length = int(sr * 0.25)
    hop_length = frame_length
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)

    energy_map = [{"time": float(t), "energy": float(v)} for t, v in zip(times, rms)]

    # ---------------------------------------------------------
    # DYNAMIC RANGE MEASUREMENT
    # ---------------------------------------------------------
    rms_linear = librosa.feature.rms(y=y)[0]
    dynamic_range = float(rms_linear.max() - rms_linear.min())

    # ---------------------------------------------------------
    # SECTION ANALYSIS (using our new chorus detector)
    # ---------------------------------------------------------
    sections = detect_chorus_sections(audio_path)

    # ---------------------------------------------------------
    # ENERGY PEAKS (transitions)
    # ---------------------------------------------------------
    peaks, _ = signal.find_peaks(rms, height=np.percentile(rms, 85))
    transitions = [float(times[p]) for p in peaks]

    return {
        "duration": float(total_duration),
        "bpm": bpm,
        "key": key,
        "scale": scale,
        "sections": sections,
        "energy_map": energy_map,
        "transitions": transitions,
        "dynamic_range": dynamic_range
    }
