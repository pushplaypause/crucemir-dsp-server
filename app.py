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

CORS(app, resources={
    r"/*": {
        "origins": [
            "https://app.base44.com",
            "https://*.base44.com",
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
    return run_demucs(request.json.get("audio_url"))

@app.post("/ffmpeg/assemble")
def ffmpeg_route():
    return run_ffmpeg_mix(request.json.get("tracks"))

@app.post("/mastering/loudness")
def mastering_route():
    return run_mastering(request.json.get("audio_url"))

@app.post("/melody/extract")
def melody_route():
    return extract_melody(request.json.get("audio_url"))

@app.post("/chord/detect")
def chord_route():
    return detect_chords(request.json.get("audio_url"))

@app.post("/dsp/analyze")
def dsp_route():
    return analyze_audio_with_librosa(request.data)


# ================================================================
#                MUSIC GENERATION (MUSICGEN)
# ================================================================
@app.post("/gen/instrumental")
def gen_instrumental():
    data = request.json
    result = generate_music(
        data.get("prompt"),
        data.get("duration", 32),
        data.get("bpm", None),
        data.get("seed", None)
    )
    return jsonify(result)


@app.post("/gen/song")
def gen_song():
    data = request.json
    style = data.get("style", "cinematic metalcore")
    emotion = data.get("emotion", "dark and emotional")
    bpm = data.get("bpm", 120)
    duration = data.get("duration", 32)

    prompt = (
        f"{style}, {emotion}, cinematic, atmospheric, metalcore, "
        "guitars, drums, ambience, cohesive structure"
    )

    return jsonify(generate_music(prompt, duration, bpm))


# ================================================================
#                     PERSONA SYSTEM
# ================================================================
@app.post("/persona/analyze")
def analyze_persona_route():
    return jsonify(analyze_persona_audio(request.data))

@app.post("/persona/cache")
def cache_persona_route():
    body = request.json
    return jsonify(cache_persona(body["persona_id"], body["persona_data"]))


# ================================================================
#                SIMPLE SOVITS (Legacy Endpoint)
# ================================================================
@app.post("/sovits/sing")
def sovits_simple_route():
    lyrics = request.json.get("lyrics")
    midi_b64 = request.json.get("melody_midi")
    persona_id = request.json.get("persona_id")

    persona = load_persona(persona_id)
    midi_bytes = midi_b64.encode("latin1") if midi_b64 else b""

    result = run_sovits(lyrics, midi_bytes, persona)
    return send_file(result["wav_path"], mimetype="audio/wav")


# ================================================================
#           ADVANCED MULTILAYER SOVITS (NEW ENDPOINT)
# ================================================================
@app.post("/sovits/sing-multi")
def sovits_multilayer_route():
    body = request.json

    lyrics = body["lyrics"]
    midi_b64 = body["melody_midi_base64"]
    persona_id = body["persona_id"]
    layers = body["layers"]  # dict {mode: weight}

    persona = load_persona(persona_id)
    midi_bytes = midi_b64.encode("latin1")

    audio_bytes = run_sovits_multilayer(lyrics, midi_bytes, persona, layers)

    tmp = f"/tmp/multi_out_{uuid.uuid4()}.wav"
    with open(tmp, "wb") as f:
        f.write(audio_bytes)

    return send_file(tmp, mimetype="audio/wav")


# ================================================================
#                     ADVANCED DSP FEATURES
# ================================================================
@app.post("/versions/save")
def save_version_route():
    return jsonify(save_version(request.json["song_id"], request.json["audio_url"]))

@app.get("/versions/list")
def list_versions_route():
    return jsonify(get_versions(request.args.get("song_id")))

@app.post("/cover/generate")
def cover_route():
    return jsonify(generate_cover(request.json["prompt"]))

@app.post("/lyrics/generate")
def lyrics_route():
    return jsonify(generate_lyrics(request.json["style"], request.json["emotion"]))

@app.post("/vocal/doubler")
def doubler_route():
    return vocal_doubler(request.data)

@app.post("/master/analog")
def analog_route():
    return analog_master(request.data)

@app.post("/automix")
def automix_route():
    return auto_mix(request.json["stems"])

@app.post("/songwriting")
def songwriting_route():
    return jsonify(songwriting_helper(request.json["style"]))

@app.post("/melody/midi")
def midi_route():
    return voice_to_midi(request.data)

@app.post("/vocal/ghost2")
def ghost2_route():
    return apply_ghost_mode(request.data)


# ================================================================
#                           ENTRYPOINT
# ================================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
