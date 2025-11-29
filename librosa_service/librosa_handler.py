import librosa
import numpy as np
import soundfile as sf
import ffmpeg
import tempfile
import requests

def download_audio_to_wav(url):
    """Download audio from URL → convert to WAV → return path."""
    response = requests.get(url, stream=True)
    response.raise_for_status()

    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
    temp_input.write(response.content)
    temp_input.flush()

    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

    (
        ffmpeg
        .input(temp_input.name)
        .output(temp_wav.name, format="wav", ac=1, ar=44100)
        .overwrite_output()
        .run(quiet=True)
    )

    return temp_wav.name


def detect_key(y, sr):
    """Simple key detection using harmonic pitch class profiles."""
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                              2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                              2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    # Major correlation
    major_corr = np.correlate(chroma_mean, major_profile)
    minor_corr = np.correlate(chroma_mean, minor_profile)

    key_index = np.argmax(chroma_mean)

    pitch_names = ['C', 'C#', 'D', 'D#', 'E', 'F',
                   'F#', 'G', 'G#', 'A', 'A#', 'B']

    if major_corr > minor_corr:
        return pitch_names[key_index] + " Major"
    else:
        return pitch_names[key_index] + " Minor"


def analyze_audio_with_librosa(audio_url):
    """
    Full DSP analysis using Librosa.
    Runs on Render without Essentia.
    """
    try:
        wav_path = download_audio_to_wav(audio_url)

        # Load audio
        y, sr = librosa.load(wav_path, sr=44100, mono=True)

        # Duration
        duration = librosa.get_duration(y=y, sr=sr)

        # Tempo (BPM)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

        # Key detection
        musical_key = detect_key(y, sr)

        # Spectral centroid (brightness)
        spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))

        # Loudness (RMS)
        rms = float(np.mean(librosa.feature.rms(y=y)))

        return {
            "status": "success",
            "dsp": {
                "duration_seconds": duration,
                "bpm": float(tempo),
                "key": musical_key,
                "brightness": spectral_centroid,
                "loudness_rms": rms
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
