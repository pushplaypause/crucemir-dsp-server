import re
import numpy as np

def analyze_lyrics_hq(text):
    """
    Deep lyrical emotion and delivery analyzer.
    """

    words = text.lower().split()
    length = len(words)

    # Darkness score
    dark_words = ["bleed", "ghost", "fade", "ruin", "shatter", "hurt", "lost"]
    dark_score = sum(1 for w in words if w in dark_words) / max(1, length)

    # Breathiness indicator
    breath_score = sum(1 for w in words if "whisper" in w or "breath" in w) / max(1, length)

    # Imagery density
    imagery = ["shadow", "night", "cold", "light", "storm", "silence", "dust"]
    imagery_score = sum(1 for w in words if w in imagery) / max(1, length)

    # Pace (syllables)
    vowels = re.findall(r"[aeiouAEIOU]", text)
    pace = len(vowels) / max(1, length)

    # Emotion categories
    if dark_score > 0.1:
        emotion = "dark / wounded"
    elif imagery_score > 0.15:
        emotion = "cinematic / atmospheric"
    else:
        emotion = "emotional / vulnerable"

    # Delivery suggestions
    delivery = {
        "whisper": breath_score > 0.05,
        "rasp": dark_score > 0.08,
        "soaring_clean": imagery_score > 0.12,
        "spoken": pace < 0.3
    }

    return {
        "emotion": emotion,
        "pace": pace,
        "imagery": imagery_score,
        "darkness": dark_score,
        "breathiness": breath_score,
        "delivery": delivery
    }
