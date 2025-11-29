import numpy as np
import librosa
import librosa.display
import scipy.signal as signal

def detect_chorus_sections(audio_path):
    """
    Modern high-accuracy chorus detector.
    Returns:
        {
          "chorus_times": [...],
          "sections": [
              {"type": "intro", "start": _, "end": _},
              {"type": "verse", ...},
              {"type": "chorus", ...},
              ...
          ]
        }
    """

    # ---------------------------------------------------------
    # Load audio
    # ---------------------------------------------------------
    y, sr = librosa.load(audio_path, sr=44100)

    # Harmonic + percussive split (chorus = harmonic-heavy)
    harmonic, percussive = librosa.effects.hpss(y)

    # ---------------------------------------------------------
    # Compute chroma for repetition analysis
    # ---------------------------------------------------------
    chroma = librosa.feature.chroma_cens(y=harmonic, sr=sr)
    chroma_smooth = signal.medfilt(chroma, kernel_size=(1, 8))

    # ---------------------------------------------------------
    # Beat sync the chroma
    # ---------------------------------------------------------
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    chroma_sync = librosa.util.sync(chroma_smooth, beats, aggregate=np.median)

    # ---------------------------------------------------------
    # Compute self-similarity matrix (SSM)
    # ---------------------------------------------------------
    ssm = librosa.segment.recurrence_matrix(
        chroma_sync,
        mode='affinity',
        sym=True
    )

    # Convert to novelty curve (high → repeated sections)
    novelty = librosa.onset.onset_strength(sr=sr, y=y)
    novelty = novelty / (np.max(novelty) + 1e-6)

    # Chorus usually has highest harmonic energy + repetition
    harmonic_energy = librosa.feature.rms(y=harmonic)[0]

    # Normalize
    harmonic_energy /= (np.max(harmonic_energy) + 1e-6)

    # ---------------------------------------------------------
    # Combine metrics: (this is the core algorithm)
    # ---------------------------------------------------------
    chorus_score = (
        0.35 * harmonic_energy +
        0.50 * ssm.mean(axis=0) +
        0.15 * novelty
    )

    # Smooth
    chorus_score = signal.medfilt(chorus_score, kernel_size=9)

    # ---------------------------------------------------------
    # Detect peaks = possible choruses
    # ---------------------------------------------------------
    peaks, _ = signal.find_peaks(
        chorus_score,
        height=np.percentile(chorus_score, 75),  # strong sections
        distance=sr * 4 / 512  # ~4 seconds
    )

    # Convert beat indices → timestamps
    beat_times = librosa.frames_to_time(beats, sr=sr)
    chorus_times = [float(beat_times[p]) for p in peaks if p < len(beat_times)]

    # ---------------------------------------------------------
    # Build section map
    # ---------------------------------------------------------
    sections = []
    last_time = 0.0

    for t in chorus_times:
        if t - last_time > 14:
            sections.append({"type": "verse", "start": last_time, "end": t})
        sections.append({"type": "chorus", "start": t, "end": t + 12})
        last_time = t + 12

    # Outro detection
    if last_time < librosa.get_duration(y=y, sr=sr):
        sections.append({
            "type": "outro",
            "start": last_time,
            "end": float(librosa.get_duration(y=y, sr=sr))
        })

    return {
        "chorus_times": chorus_times,
        "sections": sections
    }
