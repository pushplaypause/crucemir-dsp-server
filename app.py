import os
import uuid
import traceback
import tempfile
import librosa
import base64
import numpy as np

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

##############################################################
# IMPORT ONLY MODULES THAT ACTUALLY EXIST IN YOUR REPO
##############################################################

# Demucs CPU separation
from demucs_service.demucs_handler import run_demucs

# FFmpeg tools
from ffmpeg_service.ffmpeg_handler import (
    run_ffmpeg_mix,
    create_zip_from_stems
)

# Mastering
from mastering_service.mastering_handler import run_mastering
from analog_master_service.analog_master_handler import analog_master
from master_ai_service.master_ai_handler import run_master_ai

# Pitch / Time
from pitch_service.pitch_handler import pitch_shift
from timestretch_service.timestretch_handler import time_stretch

# Effects
from ghost_mode_service.ghost_mode_handler import apply_ghost_mode
from doubler_service.doubler_handler import vocal_doubler

# Melody / MIDI extraction
from melody_midi_service.melody_midi_handler import voice_to_midi

# Persona cache
from persona_service.persona_cache import cache_persona, load_persona

# Sovits
from sovits_service.sovits_handler import run_sovits
from sovits_service.sovits_multilayer import run_sovits_multilayer

# MusicGen simple
from musicgen_service.musicgen_handler import generate_music

# Cover art
from cover_art_service.cover_art_handler import generate_cover

# Versions
from versioning_service.version_handler import save_version, get_versions

# DSP utils
from dsp_service.dsp_utils import (
    detect_onsets,
    estimate_tempo,
    compute_energy_map,
    detect_silence,
    slice_by_onsets,
    detect_transients
)

##############################################################
# SAFE FALLBACKS FOR MODULES NOT IN YOUR REPO
##############################################################

def safe_not_implemented(*args, **kwargs):
    return {"status": "not_implemented"}

# Missing advanced modules overridden with safe versions
analyze_song = safe_not_implemented
align_lyrics_to_melody = safe_not_implemented
detect_chorus_sections = safe_not_implemented
musicgen_hq = safe_not_implemented
master_instrumental_hq = safe_not_implemented
analyze_persona_hq = safe_not_implemented
build_vocal_chain_preset = safe_not_implemented
master_album_hq = safe_not_implemented
sovits_multipass_hq = safe_not_implemented
analyze_lyrics_hq = safe_not_implemented
songwriting_hq = safe_not_implemented
create_hq_zip_stems = lambda stems: b"EMPTY_ZIP"

##############################################################
# FLASK APP SETUP
##############################################################

app = Flask(__name__)

##############################################################
# STATIC FILES
##############################################################

@app.route("/files/<path:filename>")
def serve_files(filename):
    path = os.path.join("/tmp", filename)
    if not os.path.exists(path):
        return jsonify({"error": "file not found"}), 404
    return send_file(path)

##############################################################
# CORS CONFIG
##############################################################

CORS(app, resources={r"/*": {"origins": "*"}})

##############################################################
# UTILS
##############################################################

def safe_json():
    return request.get_json(silent=True) or {}

def error_response(e):
    print("------ ERROR ------")
    print(traceback.format_exc())
    return jsonify({"error": str(e)}), 500

def generate_temp_file(raw_bytes, ext=".wav"):
    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join("/tmp", name)
    with open(path, "wb") as f:
        f.write(raw_bytes)
    url = f"{request.url_root.rstrip('/')}/files/{name}"
    return path, url

##############################################################
# HEALTHCHECK
##############################################################

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

##############################################################
# DSP: Onsets
##############################################################

@app.post("/dsp/onsets")
def dsp_onsets_route():
    try:
        audio_bytes = request.data
        temp = tempfile.mktemp(suffix=".wav")
        with open(temp, "wb") as f:
            f.write(audio_bytes)

        audio, sr = librosa.load(temp, sr=44100)
        result = detect_onsets(audio, sr)
        return jsonify({"onsets": result})
    except Exception as e:
        return error_response(e)

##############################################################
# SONG ANALYSIS (Fallback)
##############################################################

@app.post("/audio/analyze")
def analyze_route():
    try:
        data = safe_json()
        url = data["audio_url"]

        tmp = tempfile.mktemp(suffix=".wav")
        import requests
        with open(tmp, "wb") as f:
            f.write(requests.get(url).content)

        result = analyze_song(tmp)
        return jsonify(result)
    except Exception as e:
        return error_response(e)

##############################################################
# CHORUS DETECTION (Fallback)
##############################################################

@app.post("/audio/chorus")
def chorus_route():
    try:
        data = safe_json()
        url = data["audio_url"]

        import requests
        tmp = tempfile.mktemp(suffix=".wav")
        with open(tmp, "wb") as f:
            f.write(requests.get(url).content)

        return jsonify(detect_chorus_sections(tmp))
    except Exception as e:
        return error_response(e)

##############################################################
# ZIP STEMS (HQ + SIMPLE)
##############################################################

@app.post("/ffmpeg/zipstems")
def zipstems_route():
    try:
        data = safe_json()
        stems = data["stems"]
        hq = request.args.get("hq") == "true"

        if hq:
            raw = create_hq_zip_stems(stems)
        else:
            raw = create_zip_from_stems(stems)

        _, url = generate_temp_file(raw, ext=".zip")
        return jsonify({"zip_url": url})
    except Exception as e:
        return error_response(e)

##############################################################
# DEMUCS CPU STEM SEPARATION
##############################################################

@app.post("/demucs/separate")
def demucs_route():
    try:
        data = safe_json()
        url = data["audio_url"]
        stems = run_demucs(url)
        return jsonify({"stems": stems})
    except Exception as e:
        return error_response(e)

##############################################################
# SOVITS SIMPLE
##############################################################

@app.post("/sovits/sing")
def sovits_sing():
    try:
        data = safe_json()
        persona = load_persona(data["persona_id"])
        lyrics = data["lyrics"]

        midi = base64.b64decode(data["melody_midi"]) if data.get("melody_midi") else b""
        result = run_sovits(lyrics, midi, persona)

        wav_path = result["wav_path"]
        url = f"{request.url_root.rstrip('/')}/files/{os.path.basename(wav_path)}"
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)

##############################################################
# SOVITS MULTILAYER
##############################################################

@app.post("/sovits/sing-multi")
def sovits_multi():
    try:
        data = safe_json()
        persona = load_persona(data["persona_id"])
        lyrics = data["lyrics"]
        midi = base64.b64decode(data["melody_midi"])
        layers = data["layers"]

        audio = run_sovits_multilayer(lyrics, midi, persona, layers)
        _, url = generate_temp_file(audio)
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)

##############################################################
# GHOST MODE
##############################################################

@app.post("/vocal/ghost2")
def ghost_route():
    try:
        data = safe_json()
        url = data["audio_url"]
        hq = request.args.get("hq") == "true"
        audio = apply_ghost_mode(url, hq=hq)
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)

##############################################################
# VOCAL DOUBLER
##############################################################

@app.post("/vocal/doubler")
def doubler_route():
    try:
        data = safe_json()
        url = data["audio_url"]
        audio = vocal_doubler(url)
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)

##############################################################
# MUSICGEN SIMPLE
##############################################################

@app.post("/gen/instrumental")
def gen_instrumental():
    try:
        data = safe_json()
        prompt = data["prompt"]
        bpm = data.get("bpm")
        duration = data.get("duration", 32)
        seed = data.get("seed")

        res = generate_music(prompt, duration, bpm, seed)
        return jsonify(res)
    except Exception as e:
        return error_response(e)

##############################################################
# ANALOG MASTERING
##############################################################

@app.post("/master/analog")
def analog_route():
    try:
        data = safe_json()
        url = data["audio_url"]
        audio = analog_master(url)
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)

##############################################################
# AI MASTERING
##############################################################

@app.post("/master/ai")
def master_ai_route():
    try:
        data = safe_json()
        url = data["audio_url"]
        preset = data.get("preset", "default")
        audio = run_master_ai(url, preset)
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)

##############################################################
# PITCH SHIFT
##############################################################

@app.post("/audio/pitch")
def pitch_route():
    try:
        data = safe_json()
        url = data["audio_url"]
        semitones = data["semitones"]
        audio = pitch_shift(url, semitones)
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)

##############################################################
# TIME STRETCH
##############################################################

@app.post("/audio/timestretch")
def timestretch_route():
    try:
        data = safe_json()
        url = data["audio_url"]
        factor = data["stretch_factor"]
        audio = time_stretch(url, factor)
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)

##############################################################
# MELODY TO MIDI
##############################################################

@app.post("/melody/midi")
def melody_midi_route():
    try:
        data = safe_json()
        url = data["audio_url"]
        midi_url = voice_to_midi(url)
        return jsonify({"midi_url": midi_url})
    except Exception as e:
        return error_response(e)

##############################################################
# PERSONA
##############################################################

@app.post("/persona/cache")
def persona_cache_route():
    try:
        data = safe_json()
        return jsonify(cache_persona(data["persona_id"], data["persona_data"]))
    except Exception as e:
        return error_response(e)

@app.post("/persona/analyze")
def persona_analyze_route():
    try:
        return jsonify(analyze_persona_hq(request.data))
    except Exception as e:
        return error_response(e)

@app.post("/persona/preset")
def persona_preset_route():
    try:
        data = safe_json()
        preset = build_vocal_chain_preset(data["persona"])
        return jsonify(preset)
    except Exception as e:
        return error_response(e)

##############################################################
# COVER ART
##############################################################

@app.post("/cover/generate")
def cover_route():
    try:
        prompt = safe_json()["prompt"]
        return jsonify(generate_cover(prompt))
    except Exception as e:
        return error_response(e)

##############################################################
# VERSIONS
##############################################################

@app.post("/versions/save")
def version_save_route():
    try:
        data = safe_json()
        return jsonify(save_version(data["song_id"], data["audio_url"]))
    except Exception as e:
        return error_response(e)

@app.get("/versions/list")
def version_list_route():
    try:
        song_id = request.args.get("song_id")
        return jsonify(get_versions(song_id))
    except Exception as e:
        return error_response(e)

##############################################################
# ENTRY POINT
##############################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
