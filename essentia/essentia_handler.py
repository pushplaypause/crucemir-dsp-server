import tempfile, os, essentia.standard as es
from flask import jsonify

def run_essentia(audio_bytes):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    audio = es.MonoLoader(filename=temp_path)()

    rhythm = es.RhythmExtractor2013(method="multifeature")
    bpm, _, _, _, _ = rhythm(audio)

    key_extractor = es.KeyExtractor()
    key, scale, strength = key_extractor(audio)

    return jsonify({
        "bpm": round(bpm),
        "key": key,
        "scale": scale,
        "strength": strength,
        "success": True
    })
