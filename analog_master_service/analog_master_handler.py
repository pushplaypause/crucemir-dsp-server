import librosa
import soundfile as sf
import numpy as np
import tempfile

def analog_master(audio_bytes):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(audio_bytes)
    tmp.close()

    y, sr = librosa.load(tmp.name, sr=44100)

    # Tape saturation
    y = np.tanh(y * 2.5)

    # Gentle tonal smoothing
    y = librosa.decompose.nn_filter(y, aggregate=np.mean)

    # Limiting
    y = y / max(np.abs(y)) * 0.98

    out = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    sf.write(out.name, y, sr)

    return open(out.name, "rb").read()
