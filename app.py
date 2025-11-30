import os
import uuid
import traceback
import tempfile
import librosa
import base64
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

###############################################################
# CORE DSP SERVICES
###############################################################
from demucs_service.demucs_handler import run_demucs
from ffmpeg_service.ffmpeg_handler import run_ffmpeg_mix, create_zip_from_stems
from mastering_service.mastering_handler import run_mastering
from master_ai_service.master_ai_handler import run_master_ai
from melody_service.melody_handler import extract_melody
from chord_service.chord_handler import detect_chords
from librosa_service.librosa_handler import analyze_audio_with_librosa
from pitch_service.pitch_handler import pitch_shift
from timestretch_service.timestretch_handler import time_stretch
from chorus_service.chorus_detector import detect_chorus_sections
from analysis_service.song_analyzer import analyze_song
from alignment_service.lyric_alignment import align_lyrics_to_melody

###############################################################
# HQ ENGINES
###############################################################
from musicgen_service.musicgen_hq import musicgen_hq
from instrumental_master_service.instrumental_master_hq import master_instrumental_hq
from persona_service.persona_analyzer_hq import analyze_persona_hq
from persona_service.vocal_presets_hq import build_vocal_chain_preset
from album_master_service.album_master_hq import master_album_hq
from sovits_service.sovits_multiengine_hq import sovits_multipass_hq
from lyrics_service.lyrics_analyzer_hq import analyze_lyrics_hq
from songwriting_service.songwriting_hq import songwriting_hq

###############################################################
# LEGACY FEATURES
###############################################################
from persona_service.persona_cache import cache_persona, load_persona
from sovits_service.sovits_handler import run_sovits
from sovits_service.sovits_multilayer import run_sovits_multilayer
from musicgen_service.musicgen_handler import generate_music
from ghost_mode_service.ghost_mode_handler import apply_ghost_mode
from analog_master_service.analog_master_handler import analog_master
from doubler_service.doubler_handler import vocal_doubler
from automix_service.automix_handler import auto_mix
from melody_midi_service.melody_midi_handler import voice_to_midi
from cover_art_service.cover_art_handler import generate_cover
from versioning_service.version_handler import save_version, get_versions

###############################################################
# FLASK + STATIC HANDLER
###############################################################
app = Flask(__name__)

@app.route("/files/<path:filename>")
def serve_files(filename):
    full = os.path.join("/tmp", filename)
    if not os.path.isfile(full):
        return jsonify({"error": "File not found"}), 404
    return send_file(full)

###############################################################
# CORS (Render + Base44 safe)
###############################################################
CORS(app, resources={
    r"/*": {
        "origins": [
            r"https://.*\.base44\.com$",
            "https://app.base44.com",
            "https://crucemir-admin.base44.com"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        return "", 200

###############################################################
# UTILS
###############################################################
def safe_json():
    return request.get_json(silent=True) or {}

def error_response(e):
    print("----- ERROR -----")
    print(traceback.format_exc())
    return jsonify({"error": str(e)}), 500

def save_temp(raw):
    path = tempfile.mktemp(suffix=".wav")
    with open(path, "wb") as f:
        f.write(raw)
    return path

def generate_temp_file(raw, ext=".wav"):
    name = f"file_{uuid.uuid4().hex}{ext}"
    path = os.path.join("/tmp", name)
    with open(path, "wb") as f:
        f.write(raw)
    url = f"{request.url_root.rstrip('/')}/files/{name}"
    return path, url

###############################################################
# HEALTH CHECK
###############################################################
@app.get("/health")
def health():
    return jsonify({"status": "ok"})

###############################################################
# ---------------------- DSP ENDPOINTS ------------------------
###############################################################

@app.post("/dsp/onsets")
def dsp_onsets_route():
    try:
        audio_bytes = request.data
        tmp = save_temp(audio_bytes)
        audio, sr = librosa.load(tmp, sr=44100)
        from dsp_service.dsp_utils import detect_onsets
        return jsonify({"onsets": detect_onsets(audio, sr)})
    except Exception as e:
        return error_response(e)


###############################################################
# ----------------- SONG ANALYZER (HQ) ------------------------
###############################################################

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



###############################################################
# ---------------------- CHORUS DETECTION ---------------------
###############################################################

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



###############################################################
# --------------------- DEMUCS STEM SPLIT ---------------------
###############################################################

@app.post("/demucs/separate")
def demucs_route():
    try:
        url = safe_json()["audio_url"]
        stems = run_demucs(url)
        return jsonify({"stems": stems})
    except Exception as e:
        return error_response(e)



###############################################################
# ------------------ ZIP STEMS (HQ OR BASIC) ------------------
###############################################################

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



###############################################################
# ----------------------- SOVITS SIMPLE -----------------------
###############################################################

@app.post("/sovits/sing")
def sovits_sing():
    try:
        data = safe_json()
        persona = load_persona(data["persona_id"])
        midi = base64.b64decode(data["melody_midi"]) if data.get("melody_midi") else b""

        result = run_sovits(data["lyrics"], midi, persona)
        wav_path = result["wav_path"]

        url = f"{request.url_root.rstrip('/')}/files/{os.path.basename(wav_path)}"
        return jsonify({"audio_url": url})
    except Exception as e:
        return error_response(e)



###############################################################
# ---------------------- SOVITS MULTI -------------------------
###############################################################

@app.post("/sovits/sing-multi")
def sovits_multi():
    try:
        data = safe_json()
        persona = load_persona(data["persona_id"])
        midi = base64.b64decode(data["melody_midi"])
        layers = data["layers"]

        audio_bytes = run_sovits_multilayer(data["lyrics"], midi, persona, layers)
        _, out_url = generate_temp_file(audio_bytes)

        return jsonify({"audio_url": out_url})
    except Exception as e:
        return error_response(e)



###############################################################
# --------------------- SOVITS MULTIPASS HQ -------------------
###############################################################

@app.post("/sovits/sing-hq")
def sovits_sing_hq():
    try:
        data = safe_json()
        persona = load_persona(data["persona_id"])
        midi = base64.b64decode(data["melody_midi"])

        audio = sovits_multipass_hq(
            data["lyrics"], 
            midi, 
            persona
        )

        _, out_url = generate_temp_file(audio)
        return jsonify({"audio_url": out_url})
    except Exception as e:
        return error_response(e)



###############################################################
# ----------------------- VOCAL EFFECTS -----------------------
###############################################################

@app.post("/vocal/ghost2")
def ghost2_route():
    try:
        url = safe_json()["audio_url"]
        hq = request.args.get("hq") == "true"

        audio = apply_ghost_mode(url, hq=hq)
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)


@app.post("/vocal/doubler")
def doubler_route():
    try:
        url = safe_json()["audio_url"]
        audio = vocal_doubler(url)
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)



###############################################################
# ------------------------ MUSICGEN HQ ------------------------
###############################################################

@app.post("/gen/song-hq")
def gen_song_hq():
    try:
        data = safe_json()
        audio = musicgen_hq(
            data["prompt"],
            data.get("duration", 32),
            data.get("bpm"),
            data.get("seed"),
        )
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)



###############################################################
# -------------------- MUSICGEN SIMPLE ------------------------
###############################################################

@app.post("/gen/instrumental")
def gen_instrumental():
    try:
        data = safe_json()
        res = generate_music(
            data["prompt"],
            data.get("duration", 32),
            data.get("bpm"),
            data.get("seed")
        )
        return jsonify(res)
    except Exception as e:
        return error_response(e)


@app.post("/gen/song")
def gen_song():
    try:
        data = safe_json()
        prompt = (
            f'{data["style"]}, {data["emotion"]}, cinematic, metalcore, '
            f'guitars, ambience, emotional structure'
        )
        result = generate_music(prompt, data.get("duration", 32), data.get("bpm", 120))
        return jsonify(result)
    except Exception as e:
        return error_response(e)



###############################################################
# ------------------------- MASTERING -------------------------
###############################################################

@app.post("/master/analog")
def analog_master_route():
    try:
        url = safe_json()["audio_url"]
        audio = analog_master(url)
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)


@app.post("/master/ai")
def master_ai_route():
    try:
        data = safe_json()
        audio = run_master_ai(data["audio_url"], data.get("preset", "default"))
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)


@app.post("/master/instrumental")
def instrumental_master_route():
    try:
        url = safe_json()["audio_url"]
        audio = master_instrumental_hq(url)
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)



###############################################################
# ---------------------- PITCH / TIMESTRETCH ------------------
###############################################################

@app.post("/audio/pitch")
def audio_pitch_route():
    try:
        data = safe_json()
        audio = pitch_shift(data["audio_url"], data["semitones"])
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)


@app.post("/audio/timestretch")
def audio_timestretch_route():
    try:
        data = safe_json()
        audio = time_stretch(data["audio_url"], data["stretch_factor"])
        _, out = generate_temp_file(audio)
        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)



###############################################################
# ------------------------- MELODY / MIDI ---------------------
###############################################################

@app.post("/melody/midi")
def melody_midi_route():
    try:
        url = safe_json()["audio_url"]
        midi_url = voice_to_midi(url)
        return jsonify({"midi_url": midi_url})
    except Exception as e:
        return error_response(e)



###############################################################
# -------------------------- PERSONA --------------------------
###############################################################

@app.post("/persona/analyze")
def persona_analyze_route():
    try:
        return jsonify(analyze_persona_hq(request.data))
    except Exception as e:
        return error_response(e)


@app.post("/persona/cache")
def persona_cache_route():
    try:
        data = safe_json()
        return jsonify(cache_persona(data["persona_id"], data["persona_data"]))
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


@app.post("/persona/preview")
def persona_preview_route():
    try:
        data = safe_json()
        persona = load_persona(data["persona_id"])
        text = data["text"]

        sr = 16000
        duration = max(1.0, len(text) * 0.11)
        t = np.linspace(0, duration, int(sr * duration))
        melody = (0.5 * np.sin(2 * np.pi * 174.6 * t)).astype(np.float32)

        result = run_sovits(text, melody.tobytes(), persona)
        wav = result["wav_path"]
        out = f"{request.url_root.rstrip('/')}/files/{os.path.basename(wav)}"

        return jsonify({"audio_url": out})
    except Exception as e:
        return error_response(e)



###############################################################
# -------------------- LYRICS / SONGWRITING -------------------
###############################################################

@app.post("/lyrics/align")
def lyrics_align_route():
    try:
        data = safe_json()
        alignment = align_lyrics_to_melody(
            data["lyrics"],
            data["bpm"],
            data["melody_length"]
        )
        return jsonify({"alignment": alignment})
    except Exception as e:
        return error_response(e)


@app.post("/lyrics/analyze")
def lyrics_analyze_route():
    try:
        text = safe_json()["text"]
        return jsonify(analyze_lyrics_hq(text))
    except Exception as e:
        return error_response(e)


@app.post("/songwriting/hq")
def songwriting_hq_route():
    try:
        data = safe_json()
        res = songwriting_hq(
            data["persona"],
            data["mood"],
            data.get("bpm", 120),
            data.get("style", "cinematic metalcore"),
        )
        return jsonify(res)
    except Exception as e:
        return error_response(e)



###############################################################
# --------------------------- COVER ART -----------------------
###############################################################

@app.post("/cover/generate")
def cover_route():
    try:
        data = safe_json()
        return jsonify(generate_cover(data["prompt"]))
    except Exception as e:
        return error_response(e)



###############################################################
# --------------------------- VERSIONS -------------------------
###############################################################

@app.post("/versions/save")
def save_version_route():
    try:
        data = safe_json()
        return jsonify(save_version(data["song_id"], data["audio_url"]))
    except Exception as e:
        return error_response(e)


@app.get("/versions/list")
def list_versions_route():
    try:
        song_id = request.args.get("song_id")
        return jsonify(get_versions(song_id))
    except Exception as e:
        return error_response(e)



###############################################################
# -------------------------- ENTRYPOINT ------------------------
###############################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
