import os
import uuid
import traceback
import tempfile
import base64
import numpy as np
import librosa

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# =====================================================================
# CORE DSP SERVICES
# =====================================================================
from demucs_service.demucs_handler import run_demucs
from ffmpeg_service.ffmpeg_handler import run_ffmpeg_mix, create_zip_from_stems
from ffmpeg_service.zip_stems_hq import create_hq_zip_stems

from mastering_service.mastering_handler import run_mastering
from master_ai_service.master_ai_handler import run_master_ai
from instrumental_master_service.instrumental_master_hq import master_instrumental_hq

from melody_service.melody_handler import extract_melody
from chord_service.chord_handler import detect_chords
from librosa_service.librosa_handler import analyze_audio_with_librosa

from pitch_service.pitch_handler import pitch_shift
from timestretch_service.timestretch_handler import time_stretch

from chorus_service.chorus_detector import detect_chorus_sections
from analysis_service.song_analyzer import analyze_song
from alignment_service.lyric_alignment import align_lyrics_to_melody

# =====================================================================
# HQ ENGINES
# =====================================================================
from musicgen_service.musicgen_hq import musicgen_hq
from persona_service.persona_analyzer_hq import analyze_persona_hq
from persona_service.vocal_presets_hq import build_vocal_chain_preset
from sovits_service.sovits_multiengine_hq import sovits_multipass_hq
from lyrics_service.lyrics_analyzer_hq import analyze_lyrics_hq
from songwriting_service.songwriting_hq import songwriting_hq

# =====================================================================
# LEGACY SERVICES
# =====================================================================
from persona_service.persona_cache import cache_persona, load_persona
from sovits_service.sovits_handler import run_sovits
from sovits_service.sovits_multilayer import run_sovits_multilayer
from musicgen_service.musicgen_handler import generate_music

from ghost_mode_service.ghost_mode_handler import apply_ghost_mode
from doubler_service.doubler_handler import vocal_doubler
from analog_master_service.analog_master_handler import analog_master

from automix_service.automix_handler import auto_mix
from melody_midi_service.melody_midi_handler import voice_to_midi

from cover_art_service.cover_art_handler import generate_cover
from versioning_service.version_handler import save_version, get_versions

# =====================================================================
# DSP Utilities
# =====================================================================
from dsp_service.dsp_utils import (
    detect_onsets,
    estimate_tempo,
    compute_energy_map,
    detect_silence,
    slice_by_onsets,
    detect_transients
)

# =====================================================================
# FLASK APP
# =====================================================================
app = Flask(__name__)

@app.route("/files/<path:filename>")
def serve_files(filename):
    path = os.path.join("/tmp", filename)
    if not os.path.isfile(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path)

CORS(app, resources={r"/*": {"origins": "*"}})

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        return "", 200

# =====================================================================
# UTILITY FUNCTIONS
# =====================================================================

def safe_json():
    return request.get_json(silent=True) or {}

def generate_temp_file(raw_bytes, ext=".wav"):
    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join("/tmp", name)
    with open(path, "wb") as f:
        f.write(raw_bytes)
    url = f"{request.url_root.rstrip('/')}/files/{name}"
    return path, url

def error_response(e):
    print("----- ERROR -----")
    print(traceback.format_exc())
    return jsonify({"error": str(e)}), 500

# =====================================================================
# HEALTH
# =====================================================================

@app.get("/health")
def health():
    return jsonify({"status": "ok"})


# =====================================================================
# DSP: ONSETS / ENERGY / TEMPO / TRANSIENTS
# =====================================================================

@app.post("/dsp/onsets")
def dsp_onsets_route():
    try:
        audio_bytes = request.data
        path, _ = generate_temp_file(audio_bytes)
        audio, sr = librosa.load(path, sr=44100)
        return jsonify({"onsets": detect_onsets(audio, sr)})
    except Exception as e:
        return error_response(e)


@app.post("/dsp/energy")
def dsp_energy_route():
    try:
        audio_bytes = request.data
        path, _ = generate_temp_file(audio_bytes)
        audio, sr = librosa.load(path, sr=44100)
        energy = compute_energy_map(audio)
        return jsonify({"energy_map": energy})
    except Exception as e:
        return error_response(e)


@app.post("/dsp/tempo")
def dsp_tempo_route():
    try:
        audio_bytes = request.data
        path, _ = generate_temp_file(audio_bytes)
        audio, sr = librosa.load(path, sr=44100)
        bpm = estimate_tempo(audio, sr)
        return jsonify({"bpm": bpm})
    except Exception as e:
        return error_response(e)


@app.post("/dsp/transients")
def dsp_transients_route():
    try:
        audio_bytes = request.data
        path, _ = generate_temp_file(audio_bytes)
        audio, sr = librosa.load(path, sr=44100)
        trans = detect_transients(audio, sr)
        return jsonify({"transients": trans})
    except Exception as e:
        return error_response(e)


# =====================================================================
# FULL SONG ANALYZER (structure, bpm, key, energy)
# =====================================================================

@app.post("/audio/analyze")
def song_analyze_route():
    try:
        url = safe_json()["audio_url"]

        import requests
        tmp = tempfile.mktemp(suffix=".wav")
        with open(tmp, "wb") as f:
            f.write(requests.get(url).content)

        result = analyze_song(tmp)
        return jsonify(result)
    except Exception as e:
        return error_response(e)


# =====================================================================
# CHORUS DETECTOR (modern DSP)
# =====================================================================

@app.post("/audio/chorus")
def chorus_route():
    try:
        url = safe_json()["audio_url"]

        import requests
        tmp = tempfile.mktemp(suffix=".wav")
        with open(tmp, "wb") as f:
            f.write(requests.get(url).content)

        result = detect_chorus_sections(tmp)
        return jsonify(result)
    except Exception as e:
        return error_response(e)


# =====================================================================
# ZIP STEMS (HQ + NORMAL)
# =====================================================================

@app.post("/ffmpeg/zipstems")
def zipstems_route():
    try:
        data = safe_json()
        stems = data["stems"]
        use_hq = request.args.get("hq") == "true"

        if use_hq:
            zip_bytes = create_hq_zip_stems(stems)
        else:
            zip_bytes = create_zip_from_stems(stems)

        _, zip_url = generate_temp_file(zip_bytes, ext=".zip")
        return jsonify({"zip_url": zip_url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# DEMUCS STEM SEPARATION
# =====================================================================

@app.post("/demucs/separate")
def demucs_route():
    try:
        audio_url = safe_json()["audio_url"]
        stems = run_demucs(audio_url)
        return jsonify({"stems": stems})
    except Exception as e:
        return error_response(e)


# =====================================================================
# MELODY TO MIDI
# =====================================================================

@app.post("/melody/midi")
def melody_midi_route():
    try:
        url = safe_json()["audio_url"]
        midi_url = voice_to_midi(url)
        return jsonify({"midi_url": midi_url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# ALIGN LYRICS → MELODY
# =====================================================================

@app.post("/lyrics/align")
def lyric_align_route():
    try:
        d = safe_json()
        alignment = align_lyrics_to_melody(
            d["lyrics"], d["bpm"], d["melody_length"]
        )
        return jsonify({"alignment": alignment})
    except Exception as e:
        return error_response(e)


# =====================================================================
# AUDIO: PITCH SHIFT
# =====================================================================

@app.post("/audio/pitch")
def audio_pitch_route():
    try:
        d = safe_json()
        audio_bytes = pitch_shift(d["audio_url"], d["semitones"])
        _, url = generate_temp_file(audio_bytes)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# AUDIO: TIMESTRETCH
# =====================================================================

@app.post("/audio/timestretch")
def audio_timestretch_route():
    try:
        d = safe_json()
        audio_bytes = time_stretch(d["audio_url"], d["stretch_factor"])
        _, url = generate_temp_file(audio_bytes)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# MUSICGEN SIMPLE
# =====================================================================

@app.post("/gen/instrumental")
def gen_instrumental():
    try:
        d = safe_json()
        res = generate_music(
            d["prompt"],
            d.get("duration", 32),
            d.get("bpm"),
            d.get("seed")
        )
        return jsonify(res)
    except Exception as e:
        return error_response(e)


@app.post("/gen/song")
def gen_song():
    try:
        d = safe_json()
        prompt = (
            f'{d["style"]}, {d["emotion"]}, cinematic, metalcore, '
            'guitars, ambience, emotional structure'
        )
        res = generate_music(prompt, d.get("duration", 32), d.get("bpm", 120))
        return jsonify(res)
    except Exception as e:
        return error_response(e)


# =====================================================================
# MUSICGEN HQ (3-pass high quality)
# =====================================================================

@app.post("/gen/song-hq")
def gen_song_hq():
    try:
        d = safe_json()
        audio = musicgen_hq(
            d["prompt"],
            d.get("duration", 32),
            d.get("bpm"),
            d.get("seed")
        )
        _, url = generate_temp_file(audio)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# SOVITS — SIMPLE
# =====================================================================

@app.post("/sovits/sing")
def sovits_sing():
    try:
        d = safe_json()
        persona = load_persona(d["persona_id"])
        midi_bytes = base64.b64decode(d["melody_midi"]) if d.get("melody_midi") else b""
        res = run_sovits(d["lyrics"], midi_bytes, persona)

        wav_path = res["wav_path"]
        url = f"{request.url_root.rstrip('/')}/files/{os.path.basename(wav_path)}"
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# SOVITS — MULTILAYER
# =====================================================================

@app.post("/sovits/sing-multi")
def sovits_multi():
    try:
        d = safe_json()
        persona = load_persona(d["persona_id"])
        midi_bytes = base64.b64decode(d["melody_midi"])
        audio_bytes = run_sovits_multilayer(
            d["lyrics"], midi_bytes, persona, d["layers"]
        )
        _, url = generate_temp_file(audio_bytes)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# SOVITS — MULTIPASS HQ
# =====================================================================

@app.post("/sovits/sing-hq")
def sovits_sing_hq():
    try:
        d = safe_json()
        persona = load_persona(d["persona_id"])
        midi_bytes = base64.b64decode(d["melody_midi"])
        audio = sovits_multipass_hq(d["lyrics"], midi_bytes, persona)
        _, url = generate_temp_file(audio)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# VOCAL FX — GHOST MODE
# =====================================================================

@app.post("/vocal/ghost2")
def ghost2_route():
    try:
        url_in = safe_json()["audio_url"]
        hq = request.args.get("hq") == "true"
        audio = apply_ghost_mode(url_in, hq=hq)
        _, url = generate_temp_file(audio)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# VOCAL FX — DOUBLER
# =====================================================================

@app.post("/vocal/doubler")
def doubler_route():
    try:
        url_in = safe_json()["audio_url"]
        audio = vocal_doubler(url_in)
        _, url = generate_temp_file(audio)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# MASTERING — ANALOG
# =====================================================================

@app.post("/master/analog")
def master_analog_route():
    try:
        url_in = safe_json()["audio_url"]
        audio = analog_master(url_in)
        _, url = generate_temp_file(audio)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# MASTERING — AI
# =====================================================================

@app.post("/master/ai")
def master_ai_route():
    try:
        d = safe_json()
        audio = run_master_ai(d["audio_url"], d.get("preset", "default"))
        _, url = generate_temp_file(audio)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# MASTERING — INSTRUMENTAL HQ
# =====================================================================

@app.post("/master/instrumental")
def instrumental_master_route():
    try:
        url_in = safe_json()["audio_url"]
        audio = master_instrumental_hq(url_in)
        _, url = generate_temp_file(audio)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)

# =====================================================================
# PERSONA ENGINE — HQ ANALYZER
# =====================================================================

@app.post("/persona/analyze")
def persona_analyze_route():
    try:
        audio_bytes = request.data
        features = analyze_persona_hq(audio_bytes)
        return jsonify(features)
    except Exception as e:
        return error_response(e)


# =====================================================================
# PERSONA CACHE (SAVE/LOAD)
# =====================================================================

@app.post("/persona/cache")
def persona_cache_route():
    try:
        d = safe_json()
        return jsonify(cache_persona(d["persona_id"], d["persona_data"]))
    except Exception as e:
        return error_response(e)


# =====================================================================
# PERSONA VOCAL PRESET BUILDER
# =====================================================================

@app.post("/persona/preset")
def persona_preset_route():
    try:
        d = safe_json()
        preset = build_vocal_chain_preset(d["persona"])
        return jsonify(preset)
    except Exception as e:
        return error_response(e)


# =====================================================================
# PERSONA PREVIEW (TEXT → MONOTONE)
# =====================================================================

@app.post("/persona/preview")
def persona_preview_route():
    try:
        d = safe_json()
        persona = load_persona(d["persona_id"])
        text = d["text"]

        # monotone melody (F3 = 174.6 Hz)
        sr = 16000
        duration = max(1.0, len(text) * 0.11)
        t = np.linspace(0, duration, int(sr * duration))
        melody = (0.5 * np.sin(2 * np.pi * 174.6 * t)).astype(np.float32)

        result = run_sovits(text, melody.tobytes(), persona)

        wav_path = result["wav_path"]
        filename = os.path.basename(wav_path)
        url = f"{request.url_root.rstrip('/')}/files/{filename}"

        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)


# =====================================================================
# LYRICS HQ ANALYZER
# =====================================================================

@app.post("/lyrics/analyze")
def lyrics_analyze_route():
    try:
        text = safe_json()["text"]
        result = analyze_lyrics_hq(text)
        return jsonify(result)
    except Exception as e:
        return error_response(e)


# =====================================================================
# HQ SONGWRITING ENGINE
# =====================================================================

@app.post("/songwriting/hq")
def songwriting_hq_route():
    try:
        d = safe_json()
        persona = d["persona"]
        mood = d["mood"]
        bpm = d.get("bpm", 120)
        style = d.get("style", "cinematic metalcore")
        res = songwriting_hq(persona, mood, bpm, style)
        return jsonify(res)
    except Exception as e:
        return error_response(e)


# =====================================================================
# COVER ART GENERATION
# =====================================================================

@app.post("/cover/generate")
def cover_route():
    try:
        d = safe_json()
        prompt = d["prompt"]
        result = generate_cover(prompt)
        return jsonify(result)
    except Exception as e:
        return error_response(e)


# =====================================================================
# VERSIONING
# =====================================================================

@app.post("/versions/save")
def save_version_route():
    try:
        d = safe_json()
        song_id = d["song_id"]
        audio_url = d["audio_url"]
        result = save_version(song_id, audio_url)
        return jsonify(result)
    except Exception as e:
        return error_response(e)


@app.get("/versions/list")
def list_versions_route():
    try:
        song_id = request.args.get("song_id")
        result = get_versions(song_id)
        return jsonify(result)
    except Exception as e:
        return error_response(e)


# =====================================================================
# FINAL ENTRYPOINT
# =====================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)


