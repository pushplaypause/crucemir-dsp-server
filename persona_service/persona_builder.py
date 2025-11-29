import os
import json
import uuid
import soundfile as sf
from sovits_service.sovits_handler import extract_sovits_features

PERSONA_DIR = "personas"

def build_persona(persona_id: str, audio_bytes: bytes):
    """
    Create a full persona:
    - Save raw audio
    - Extract SoVITS features
    - Save persona metadata
    """
    folder = f"{PERSONA_DIR}/{persona_id}"
    os.makedirs(folder, exist_ok=True)

    # Save voice sample
    audio_path = f"{folder}/voice.wav"
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)

    # Extract features using SoVITS
    features_json = extract_sovits_features(audio_path)

    persona_data = {
        "persona_id": persona_id,
        "features_path": features_json
    }

    json.dump(persona_data, open(f"{folder}/persona.json", "w"))

    return persona_data
