import numpy as np
import librosa
import re

# ---------------------------------------------------------
# Utility: simple syllable splitter (English)
# ---------------------------------------------------------
def split_syllables(word):
    # Basic vowel-based heuristic
    vowels = "aeiouy"
    syllables = []
    current = ""

    for i, c in enumerate(word.lower()):
        current += c
        if c in vowels:
            # syllable boundary
            if i < len(word) - 1 and word[i+1] not in vowels:
                syllables.append(current)
                current = ""
    if current:
        syllables.append(current)

    return syllables if syllables else [word]


# ---------------------------------------------------------
# Core Alignment Function
# ---------------------------------------------------------
def align_lyrics_to_melody(lyrics, bpm, melody_length, pause_ratio=0.15):
    """
    Aligns lyrics → melody beats.
    Inputs:
        lyrics: full text
        bpm: tempo of instrumental
        melody_length: number of "notes" or beats to fill
        pause_ratio: % of time to insert pauses
    Returns:
        list of { "syllable": ..., "start": ..., "end": ... }
    """

    # -----------------------------------------------------
    # Step 1: Tokenize → words → syllables
    # -----------------------------------------------------
    words = re.findall(r"[A-Za-z’']+", lyrics)
    syllables = []
    for w in words:
        syllables.extend(split_syllables(w))

    total_syllables = len(syllables)

    # -----------------------------------------------------
    # Step 2: Compute beat timing
    # -----------------------------------------------------
    seconds_per_beat = 60.0 / bpm
    total_duration = melody_length * seconds_per_beat

    # Duration per syllable (minus pauses)
    usable_duration = total_duration * (1.0 - pause_ratio)
    syllable_dur = usable_duration / total_syllables

    # -----------------------------------------------------
    # Step 3: Build alignment map
    # -----------------------------------------------------
    alignment = []
    t = 0.0

    for s in syllables:
        start = t
        end = t + syllable_dur
        alignment.append({
            "syllable": s,
            "start": float(start),
            "end": float(end)
        })
        t = end

    # -----------------------------------------------------
    # Step 4: Insert pauses (breath / phrasing)
    # -----------------------------------------------------
    pause_total_time = total_duration - usable_duration
    pause_time = pause_total_time / max(1, total_syllables // 4)

    # Add pause after every line / large word
    for i in range(3, len(alignment), 4):
        alignment[i]["end"] += pause_time
        # Shift following items
        for j in range(i+1, len(alignment)):
            shift = alignment[i]["end"] - alignment[i]["start"]
            alignment[j]["start"] += pause_time
            alignment[j]["end"] += pause_time

    return alignment
