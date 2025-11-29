import librosa
import soundfile as sf
import tempfile
import numpy as np
import scipy.signal as signal

def apply_ghost_mode(audio_bytes):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(audio_bytes)
    tmp.close()

    y, sr = librosa.load(tmp.name, sr=44100)

    breath = signal.lfilter([1, -1], [1], y)
    breath = librosa.effects.preemphasis(breath)

    harm = librosa.effects.harmonic(y)
    harm *= 1.4

    ghost = (y * 0.6 + breath * 0.4 + harm * 0.3)
    ghost = ghost / max(np.abs(ghost))

    out = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    sf.write(out.name, ghost, sr)

    return open(out.name, "rb").read()
