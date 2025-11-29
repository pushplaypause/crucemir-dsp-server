import librosa
import soundfile as sf
import numpy as np
import tempfile
import os

def vocal_doubler(audio_bytes):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(audio_bytes)
    tmp.close()

    y, sr = librosa.load(tmp.name, sr=44100)

    shifted = librosa.effects.pitch_shift(y, sr, n_steps=3)
    delayed = np.pad(y, (200, 0))

    doubled = (y + shifted * 0.5 + delayed * 0.3) / 1.8

    out = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    sf.write(out.name, doubled, sr)

    return open(out.name, "rb").read()
