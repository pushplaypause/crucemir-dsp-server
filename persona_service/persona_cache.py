import os
import json

PERSONA_DIR = "personas"

def cache_persona(persona_id, persona_data):
    folder = f"{PERSONA_DIR}/{persona_id}"
    os.makedirs(folder, exist_ok=True)

    json.dump(persona_data, open(f"{folder}/persona.json", "w"))

    return {"status": "cached", "persona_id": persona_id}


def load_persona(persona_id):
    path = f"{PERSONA_DIR}/{persona_id}/persona.json"
    if not os.path.exists(path):
        raise Exception("Persona not found")

    return json.load(open(path))
