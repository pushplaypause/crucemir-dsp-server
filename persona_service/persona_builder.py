import os
import json
import subprocess
from sovits_service.sovits_handler import extract_sovits_features

PERSONA_DIR = "/app/personas"

def build_persona(persona_id: str, audio_bytes):
    persona_path = os.path.join(PERSONA_DIR, persona_id)
    os.makedirs(persona_path, exist_ok=True)

    # Save raw audio
    wav_path = os.path.join(persona_path, "voice.wav")
    with open(wav_path, "wb") as f:
        f.write(audio_bytes)

    # Extract SoVITS conditioning
    features = extract_sovits_features(wav_path)
    feature_path = os.path.join(persona_path, "features.json")
    json.dump(features, open(feature_path, "w"))

    # Create OpenVoice embedding
    pt_output = os.path.join(persona_path, "voice.pt")

    try:
        cmd = [
            "openvoice",
            "--input", wav_path,
            "--embed",
            "--output", pt_output
        ]

        subprocess.run(cmd, check=True)
        openvoice_status = "ok"

    except Exception as e:
        openvoice_status = f"OpenVoice error: {str(e)}"

    return {
        "persona_id": persona_id,
        "status": "ready",
        "sovits_features": features,
        "openvoice_embedding": openvoice_status,
        "paths": {
            "wav": wav_path,
            "features": feature_path,
            "pt": pt_output
        }
    }
