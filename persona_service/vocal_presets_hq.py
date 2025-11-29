def build_vocal_chain_preset(persona):
    """
    Creates EQ/Comp/Reverb/Saturation presets based on persona fingerprint.
    """

    brightness = persona.get("timbre_brightness", 3000)
    breath = persona.get("breathiness", 0.05)
    vibrato = persona.get("vibrato_depth", 0.1)

    preset = {
        "eq": {
            "low_cut": 80,
            "presence_boost": 4.0 if brightness < 2800 else 2.0,
            "air_shelf": 5.0 if breath > 0.1 else 3.0
        },
        "compression": {
            "ratio": 3.5 if vibrato < 0.1 else 2.5,
            "attack": 10,
            "release": 90
        },
        "saturation": {
            "tube": 0.2,
            "tape": 0.15
        },
        "reverb": {
            "size": 0.6 if breath > 0.1 else 0.4,
            "predelay": 15
        }
    }

    return preset
