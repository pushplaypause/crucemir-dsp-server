import tempfile
import requests
import numpy as np
import soundfile as sf
import librosa
import crepe
from midiutil import MIDIFile
import scipy.signal as signal


# ------------------------------------------------------------
# FAST MODE (current behavior)
# ------------------------------------------------------------
def _melody_fast(audio_url):
    input_path = tempfile.mktemp(suffix=".wav")

    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    audio, sr = librosa.load(input_path, sr=16000)

    time, freq, conf, _ = crepe.predict(audio, sr, viterbi=True)

    valid = freq[(conf > 0.6)]
    times_valid = time[(conf > 0.6)]

    output_path = tempfile.mktemp(suffix=".mid")
    mf = MIDIFile(1)
    mf.addTempo(0, 0, 120)

    last_note = None
    for t, f0 in zip(times_valid, valid):
        if f0 <= 0:
            continue
        midi_note = int(round(69 + 12 * np.log2(f0 / 440.0)))
        if midi_note != last_note:
            mf.addNote(0, 0, midi_note, float(t), 0.25, 100)
            last_note = midi_note

    with open(output_path, "wb") as outf:
        mf.writeFile(outf)

    return output_path


# ------------------------------------------------------------
# HQ MODE (full AI-grade smoothing + CREPE full)
# ------------------------------------------------------------
def _melody_hq(audio_url):
    input_path = tempfile.mktemp(suffix=".wav")
    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    # -------------------------------------------------------
    # Load audio
    # -------------------------------------------------------
    audio, sr = librosa.load(input_path, sr=16000)

    # CREPE full precision
    time, freq, conf, _ = crepe.predict(
        audio,
        sr,
        model_capacity='full',   # much more accurate
        step_size=5,             # fine resolution
        viterbi=True
    )

    # -------------------------------------------------------
    # Confidence Filtering
    # -------------------------------------------------------
    freq[conf < 0.4] = 0  # remove weak guesses

    # -------------------------------------------------------
    # Median smoothing (removes micro jumps)
    # -------------------------------------------------------
    freq_smoothed = signal.medfilt(freq, kernel_size=7)

    # -------------------------------------------------------
    # REST detection
    # -------------------------------------------------------
    is_rest = freq_smoothed < 1
    freq_smoothed[is_rest] = 0

    # -------------------------------------------------------
    # Convert to MIDI notes
    # -------------------------------------------------------
    midi_notes = np.zeros_like(freq_smoothed, dtype=int)

    for i, f in enumerate(freq_smoothed):
        if f <= 0:
            midi_notes[i] = -1
        else:
            midi_notes[i] = int(round(69 + 12 * np.log2(f / 440.0)))

    # -------------------------------------------------------
    # Write clean MIDI events
    # -------------------------------------------------------
    output_path = tempfile.mktemp(suffix=".mid")
    mf = MIDIFile(1)
    mf.addTempo(0, 0, 120)

    last_note = -1
    note_start_time = None

    for i, note in enumerate(midi_notes):
        t = float(time[i])

        if note != last_note:
            # close off previous note
            if last_note >= 0 and note_start_time is not None:
                duration = t - note_start_time
                mf.addNote(0, 0, last_note, note_start_time, duration, 90)

            # start new note
            if note >= 0:
                note_start_time = t
            last_note = note

    # close final note
    if last_note >= 0 and note_start_time is not None:
        duration = float(time[-1]) - note_start_time
        mf.addNote(0, 0, last_note, note_start_time, duration, 90)

    with open(output_path, "wb") as outf:
        mf.writeFile(outf)

    return output_path


# ------------------------------------------------------------
# PUBLIC ENTRYPOINT
# ------------------------------------------------------------
def voice_to_midi(audio_url, hq=False):
    """
    Called by app.py
    hq=True → run HQ melody extractor
    """
    if isinstance(hq, str) and hq.lower() in ["1", "true", "yes", "y", "hq"]:
        return _melody_hq(audio_url)

    return _melody_fast(audio_url)
