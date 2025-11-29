# persona_service/persona_cache.py

import os
import json

CACHE_DIR = "/app/cache/personas"

os.makedirs(CACHE_DIR, exist_ok=True)

def cache_persona(persona_id, persona_data):
    try:
        path = os.path.join(CACHE_DIR, f"{persona_id}.json")
        with open(path, "w") as f:
            json.dump(persona_data, f)
        return {"cached": True, "persona_id": persona_id}
    except Exception as e:
        return {"error": str(e)}

def load_persona(persona_id):
    try:
        path = os.path.join(CACHE_DIR, f"{persona_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)
    except:
        return None
