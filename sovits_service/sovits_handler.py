import uuid
import json
import subprocess
import tempfile
import os
import soundfile as sf

# -----------------------------------------------------
# ADVANCED SOVITS SINGING ENGINE
# -----------------------------------------------------

def extract_sovits_features(audio_path: str):
    """
    Extract conditioning embeddings for SoVITS.
    Uses the SoVITS CLI extractor.
    """

    tmp_json = f"/tmp/sovits_features_{uuid.uuid4()}.json"

    cmd = [
        "sovits-cli",
        "extract",
        "--input", audio_path,
        "--output", tmp_json
    ]

    subprocess.run(cmd, check=True)

    return tmp_json


def run_sovits_singing(lyrics: str, midi_data: bytes, persona: dict, vocal_mode="neutral"):
    """
    Run SoVITS singing:
    - lyrics.txt
    - melody.mid (raw bytes)
    - persona features.json
    - vocal mode (0–3)
    """

    # Temp paths
    tmp_lyrics = f"/tmp/lyrics_{uuid.uuid4()}.txt"
    tmp_midi = f"/tmp/midi_{uuid.uuid4()}.mid"
    output_wav = f"/tmp/sovits_{uuid.uuid4()}.wav"

    # Save lyrics
    with open(tmp_lyrics, "w") as f:
        f.write(lyrics)

    # Save MIDI (raw bytes)
    with open(tmp_midi, "wb") as f:
        f.write(midi_data)

    # Resolve persona features path
    features_path = persona["features_path"]

    # Vocal mode mapping
    mode_map = {
        "neutral": "0",
        "whisper": "1",
        "ghost": "2",
        "aggressive": "3"
    }

    mode_code = mode_map.get(vocal_mode, "0")

    # Build command
    cmd = [
        "sovits-cli",
        "sing",
        "--lyrics", tmp_lyrics,
        "--midi", tmp_midi,
        "--features", features_path,
        "--vocal-mode", mode_code,
        "--output", output_wav
    ]

    subprocess.run(cmd, check=True)

    # Return rendered WAV as bytes
    audio_bytes, sr = sf.read(output_wav, dtype='float32')
    return audio_bytes.tobytes()
