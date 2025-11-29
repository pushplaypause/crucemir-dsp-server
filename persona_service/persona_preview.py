# persona_service/persona_preview.py

from openvoice_cli import TTS
from persona_service.persona_cache import load_persona

def preview_voice(persona_id, text):
    persona = load_persona(persona_id)
    if not persona:
        return {"error": "Persona not found"}

    tts = TTS(
        voice_preset=persona["base_voice_type"],
        timbre=persona["timbre_vector"],
        breathiness=persona["breathiness"],
        grit=persona["grit"]
    )

    output_path = "/app/cache/previews/preview.wav"
    tts.generate(text, output_path)

    with open(output_path, "rb") as f:
        data = f.read()

    return data
