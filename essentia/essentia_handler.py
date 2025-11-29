import essentia
import essentia.streaming as es
import numpy as np
import tempfile
import os
import subprocess

def run_essentia(audio_path):
    # Convert audio to mono 44.1kHz WAV for Essentia compatibility
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    subprocess.run([
        "ffmpeg", "-y",
        "-i", audio_path,
        "-ac", "1",
        "-ar", "44100",
        tmp_wav
    ], check=True)

    loader = es.MonoLoader(filename=tmp_wav)
    rhythm = es.RhythmExtractor2013(method="multifeature")
    key = es.KeyExtractor()

    pool = essentia.Pool()

    loader.audio >> rhythm.audio
    rhythm.bpm >> (lambda x: pool.add("bpm", x))
    loader.audio >> key.audio
    key.key >> (lambda x: pool.add("key", x))
    key.scale >> (lambda x: pool.add("scale", x))

    essentia.run(loader)

    bpm = float(pool["bpm"][0])
    key_val = pool["key"][0]
    scale = pool["scale"][0]

    return {
        "bpm": bpm,
        "key": key_val,
        "scale": scale
    }
