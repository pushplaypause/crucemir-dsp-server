import numpy as np
import soundfile as sf
import tempfile

def auto_mix(stem_paths):
    mix = None
    sr = None

    for s in stem_paths:
        y, sr = sf.read(s)
        rms = np.sqrt(np.mean(y**2))
        gain = 0.1 / rms if rms > 0 else 1

        y = y * gain
        mix = y if mix is None else mix + y

    mix = mix / max(np.abs(mix))

    out = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    sf.write(out.name, mix, sr)

    return open(out.name, "rb").read()
