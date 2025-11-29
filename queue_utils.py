import os
import uuid
import traceback
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# ------------------------ CORE DSP SERVICES ------------------------
from demucs_service.demucs_handler import run_demucs
from ffmpeg_service.ffmpeg_handler import run_ffmpeg_mix
from mastering_service.mastering_handler import run_mastering
from melody_service.melody_handler import extract_melody
from chord_service.chord_handler import detect_chords
from librosa_service.librosa_handler import analyze_audio_with_librosa

# Music generation
from musicgen_service.musicgen_handler import generate_music

# ------------------------ PERSONA SYSTEM ------------------------
from persona_service.persona_analyzer import analyze_persona_audio
from persona_service.persona_cache import cache_persona, load_persona

# Simple SoVITS
from sovits_service.sovits_handler import run_sovits

# Advanced multilayer SoVITS
from sovits_service.sovits_multilayer import run_sovits_multilayer

# ------------------------ ADVANCED FEATURES ------------------------
from versioning_service.version_handler import save_version, get_versions
from cover_art_service.cover_art_handler import generate_cover
from lyrics_service.lyrics_handler import generate_lyrics
from doubler_service.doubler_handler import vocal_doubler
from analog_master_service.analog_master_handler import analog_master
from automix_service.automix_handler import auto_mix
from songwriting_service.songwriting_handler import songwriting_helper
from melody_midi_service.melody_midi_handler import voice_to_midi
from ghost_mode_service.ghost_mode_handler import apply_ghost_mode



# ================================================================
#                    FLASK APP SETUP
# ================================================================
app = Flask(__name__)

# Proper wildcard CORS (regex-based)
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


# ================================================================
#                   ERROR HANDLING HELPERS
# ================================================================
def safe_json():
    if not request.is_json:
        return None
    return request.get_json(silent=True)


def error_response(e):
    print("----- ERROR -----")
    print(traceback.format_exc())
    return jsonify({"error": str(e)}), 500


# ================================================================
#                       HEALTH CHECK
# ================================================================
@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "crucemir-dsp-server",
        "endpoints": [
            "/demucs/separate",
            "/ffmpeg/assemble",
            "/mastering/loudness",
            "/melody/extract",
            "/chord/detect",
            "/sovits/sing",
            "/sovits/sing-multi",
            "/dsp/analyze",
            "/gen/instrumental",
            "/gen/song",
            "/persona/analyze",
            "/persona/cache",
            "/versions/save",
            "/versions/list",
            "/cover/generate",
            "/lyrics/generate",
            "/vocal/doubler",
            "/master/analog",
            "/automix",
            "/songwriting",
            "/melody/midi",
            "/vocal/ghost2"
        ]
    })


# ================================================================
#                      CORE DSP ENDPOINTS
# ================================================================
@app.post("/demucs/separate")
def demucs_route():
    try:
        data = safe_json()
        return run_demucs(data.get("audio_url"))
    except Exception as e:
        return error_response(e)


@app.post("/ffmpeg/assemble")
def ffmpeg_route():
    try:
        return run_ffmpeg_mix(safe_json().get("tracks"))
    except Exception as e:
        return error_response(e)


@app.post("/mastering/loudness")
def mastering_route():
    try:
        return run_mastering(safe_json().get("audio_url"))
    except Exception as e:
        return error_response(e)


@app.post("/melody/extract")
def melody_route():
    try:
        return extract_melody(safe_json().get("audio_url"))
    except Exception as e:
        return error_response(e)


@app.post("/chord/detect")
def chord_route():
    try:
        return detect_chords(safe_json().get("audio_url"))
    except Exception as e:
        return error_response(e)


@app.post("/dsp/analyze")
def dsp_route():
    try:
        return analyze_audio_with_librosa(request.data)
    except Exception as e:
        return error_response(e)



# ================================================================
#                MUSIC GENERATION (MUSICGEN)
# ================================================================
@app.post("/gen/instrumental")
def gen_instrumental():
    try:
        data = safe_json()
        result = generate_music(
            data.get("prompt"),
            data.get("duration", 32),
            data.get("bpm", None),
            data.get("seed", None)
        )
        return jsonify(result)
    except Exception as e:
        return error_response(e)


@app.post("/gen/song")
def gen_song():
    try:
        data = safe_json()
        style = data.get("style", "cinematic metalcore")
        emotion = data.get("emotion", "dark and emotional")
        bpm = data.get("bpm", 120)
        duration = data.get("duration", 32)

        prompt = (
            f"{style}, {emotion}, cinematic, atmospheric, metalcore, "
            "guitars, drums, ambience, cohesive structure"
        )

        return jsonify(generate_music(prompt, duration, bpm))
    except Exception as e:
        return error_response(e)



# ================================================================
#                     PERSONA SYSTEM
# ================================================================
@app.post("/persona/analyze")
def analyze_persona_route():
    try:
        return jsonify(analyze_persona_audio(request.data))
    except Exception as e:
        return error_response(e)


@app.post("/persona/cache")
def cache_persona_route():
    try:
        body = safe_json()
        return jsonify(cache_persona(body["persona_id"], body["persona_data"]))
    except Exception as e:
        return error_response(e)



# ================================================================
#                SIMPLE SOVITS (Legacy Endpoint)
# ================================================================
@app.post("/sovits/sing")
def sovits_simple_route():
    try:
        data = safe_json()
        lyrics = data.get("lyrics")
        midi_b64 = data.get("melody_midi")
        persona_id = data.get("persona_id")

        persona = load_persona(persona_id)
        midi_bytes = midi_b64.encode("latin1") if midi_b64 else b""

        output = run_sovits(lyrics, midi_bytes, persona)

        return send_file(output["wav_path"], mimetype="audio/wav", as_attachment=True)
    except Exception as e:
        return error_response(e)



# ================================================================
#           ADVANCED MULTILAYER SOVITS (NEW ENDPOINT)
# ================================================================
@app.post("/sovits/sing-multi")
def sovits_multilayer_route():
    try:
        body = safe_json()

        lyrics = body["lyrics"]
        midi_b64 = body["melody_midi_base64"]
        persona_id = body["persona_id"]
        layers = body["layers"]  # dict {mode: weight}

        persona = load_persona(persona_id)
        midi_bytes = midi_b64.encode("latin1")

        audio_bytes = run_sovits_multilayer(lyrics, midi_bytes, persona, layers)

        tmp = f"/tmp/multi_out_{uuid.uuid4().hex}.wav"
        with open(tmp, "wb") as f:
            f.write(audio_bytes)

        response = send_file(tmp, mimetype="audio/wav", as_attachment=True)

        # Auto-clean temp file after response finishes
        @response.call_on_close
        def cleanup():
            if os.path.exists(tmp):
                os.remove(tmp)

        return response

    except Exception as e:
        return error_response(e)



# ================================================================
#                     ADVANCED DSP FEATURES
# ================================================================
@app.post("/versions/save")
def save_version_route():
    try:
        return jsonify(save_version(safe_json()["song_id"], safe_json()["audio_url"]))
    except Exception as e:
        return error_response(e)


@app.get("/versions/list")
def list_versions_route():
    try:
        return jsonify(get_versions(request.args.get("song_id")))
    except Exception as e:
        return error_response(e)


@app.post("/cover/generate")
def cover_route():
    try:
        return jsonify(generate_cover(safe_json()["prompt"]))
    except Exception as e:
        return error_response(e)


@app.post("/lyrics/generate")
def lyrics_route():
    try:
        data = safe_json()
        return jsonify(generate_lyrics(data["style"], data["emotion"]))
    except Exception as e:
        return error_response(e)


@app.post("/vocal/doubler")
def doubler_route():
    try:
        return vocal_doubler(request.data)
    except Exception as e:
        return error_response(e)


@app.post("/master/analog")
def analog_route():
    try:
        return analog_master(request.data)
    except Exception as e:
        return error_response(e)


@app.post("/automix")
def automix_route():
    try:
        return auto_mix(safe_json()["stems"])
    except Exception as e:
        return error_response(e)


@app.post("/songwriting")
def songwriting_route():
    try:
        return jsonify(songwriting_helper(safe_json()["style"]))
    except Exception as e:
        return error_response(e)


@app.post("/melody/midi")
def midi_route():
    try:
        return voice_to_midi(request.data)
    except Exception as e:
        return error_response(e)


@app.post("/vocal/ghost2")
def ghost2_route():
    try:
        return apply_ghost_mode(request.data)
    except Exception as e:
        return error_response(e)



# ================================================================
#                           ENTRYPOINT
# ================================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
