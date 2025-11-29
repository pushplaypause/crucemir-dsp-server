import base64
from sovits_service.sovits_handler import run_sovits
from sovits_service.sovits_enhancer import enhance_sovits
from ghost_mode_service.ghost_mode_hq import ghost_mode_hq
from lyrics_service.lyrics_analyzer_hq import analyze_lyrics_hq

def sovits_multipass_hq(lyrics, midi_bytes, persona):
    """
    Multi-pass SoVITS: clarity → emotion → ghost → enhancer.
    """

    # Emotion analysis
    analysis = analyze_lyrics_hq(lyrics)
    breathy = analysis["breathiness"] > 0.05
    dark = analysis["darkness"] > 0.08

    # ------------------------------
    # PASS 1: CLARITY
    # ------------------------------
    base = run_sovits(lyrics, midi_bytes, persona)["wav_bytes"]

    # ------------------------------
    # PASS 2: EMOTION
    # add breath/rasp via enhancer weighting
    # ------------------------------
    emo_mix = enhance_sovits(base)

    # ------------------------------
    # PASS 3: GHOST LAYER
    # ------------------------------
    ghost = ghost_mode_hq(None)  # ghost from silence → texture  
    # Blend ghost layer
    import numpy as np
    ghost_wav = ghost * 0.15
    combined = emo_mix[:len(ghost_wav)] + ghost_wav

    # ------------------------------
    # PASS 4: ENHANCER
    # ------------------------------
    final = enhance_sovits(combined)

    return final
