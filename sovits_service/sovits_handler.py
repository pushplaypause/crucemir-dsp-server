import os
import json
import uuid
import base64
import subprocess
import tempfile
import soundfile as sf


PERSONA_DIR = "/app/personas"


# ---------------------------------------------------------
# EXTRACT SOVITS FEATURES
# ---------------------------------------------------------
def extract_sovits_features(audio_path: str):
    """
    Extract SoVITS conditioning features (F0, timbre, spectral).
    Calls SoVITS CLI extractor.
    """

    tmp_json = f"/tmp/sovits_features_{uuid.uuid4()}.json"

    cmd = [
        "sovits-cli",
        "extract",
        "--input", audio_path,
        "--output", tmp_json
    ]

    subprocess.run(cmd, check=True)

    return json.load(open(tmp_json))


# ---------------------------------------------------------
# RUN SOVITS SINGING WITH PERSONA + MIDI + VOCAL MODE
# ---------------------------------------------------------
def run_sovits(lyrics: str, midi_data: str, persona: dict, vocal_mode="neutral"):
    """
    Main SoVITS singing pipeline.

    Inputs:
        - lyrics: text
        - midi_data: Base64 string
        - persona: dict from persona_cache
        - vocal_mode: whisper/ghost/aggressive/neutral

    Output:
        - raw WAV bytes
    """

    # Temp files
    tmp_txt = f"/tmp/lyrics_{uuid.uuid4()}.txt"
    tmp_midi = f"/tmp/melody_{uuid.uuid4()}.mid"
    output_wav = f"/tmp/sovits_{uuid.uuid4()}.wav"

    # -----------------------------
    # Write lyrics
    # -----------------------------
    with open(tmp_txt, "w") as f:
        f.write(lyrics)

    # -----------------------------
    # Decode Base64 MIDI
    # -----------------------------
    try:
        midi_bytes = base64.b64decode(midi_data)
    except Exception:
        return {
            "success": False,
            "error": "MIDI data is not valid Base64."
        }

    with open(tmp_midi, "wb") as f:
        f.write(midi_bytes)

    # -----------------------------
    # Get persona feature paths
    # -----------------------------
    try:
        features_path = persona["paths"]["features"]
        pt_path = persona["paths"]["pt"]
    except:
        return {
            "success": False,
            "error": "Persona object missing required feature paths."
        }

    # -----------------------------
    # Vocal Mode Mapping
    # -----------------------------
    mode_map = {
        "neutral": "0",
        "whisper": "1",
        "ghost": "2",
        "aggressive": "3"
    }
    mode_code = mode_map.get(vocal_mode, "0")

    # -----------------------------
    # Build SoVITS CLI command
    # -----------------------------
    cmd = [
        "sovits-cli",
        "sing",
        "--lyrics", tmp_txt,
        "--midi", tmp_midi,
        "--features", features_path,
        "--voice-embed", pt_path,
        "--vocal-mode", mode_code,
        "--output", output_wav
    ]

    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        return {
            "success": False,
            "error": f"SoVITS failed: {str(e)}"
        }

    # -----------------------------
    # Return audio bytes
    # -----------------------------
    try:
        with open(output_wav, "rb") as f:
            audio_bytes = f.read()

        return audio_bytes

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read output audio: {str(e)}"
        }
