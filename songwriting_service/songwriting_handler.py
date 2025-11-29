import numpy as np

def songwriting_hq(persona, mood, bpm, style):
    """
    Persona-aware songwriting engine.
    Creates structure + emotional map.
    """

    # Persona features
    bright = persona.get("timbre_brightness", 3000)
    breath = persona.get("breathiness", 0.05)
    vibrato = persona.get("vibrato_rate", 0.1)
    loudness = persona.get("loudness", -20)

    # Emotional axis
    emotion_map = {
        "bright": "soaring / uplifted",
        "breathy": "intimate / vulnerable",
        "neutral": "steady / grounded"
    }

    if breath > 0.12:
        vocal_emotion = emotion_map["breathy"]
    elif bright > 2500:
        vocal_emotion = emotion_map["bright"]
    else:
        vocal_emotion = emotion_map["neutral"]

    # Structure generation
    structure = [
        "Intro (ambient pad + texture)",
        "Verse 1 (close, cinematic, low dynamics)",
        "Pre-Chorus (tension rise, rhythmic push)",
        "Chorus (wide, soaring, emotional peak)",
        "Verse 2 (contrast, variation)",
        "Bridge (haunting, atmospheric, breakdown-ready)",
        "Final Chorus (bigger, emotional, lifted)",
        "Outro (ghost-layer fade)"
    ]

    # Melody curve
    melody_shape = {
        "verse":  "descending / intimate",
        "chorus": "ascending / anthemic",
        "bridge": "oscillating / tension"
    }

    return {
        "structure": structure,
        "melody_shape": melody_shape,
        "vocal_emotion": vocal_emotion,
        "bpm": bpm,
        "style": style,
        "mood": mood
    }
