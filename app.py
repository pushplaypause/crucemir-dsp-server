from flask import Flask, request, jsonify
from flask_cors import CORS

# ------------------------ IMPORT SERVICES ------------------------
from demucs_service.demucs_handler import run_demucs
from ffmpeg_service.ffmpeg_handler import run_ffmpeg_mix
from mastering_service.mastering_handler import run_mastering
from melody_service.melody_handler import extract_melody
from chord_service.chord_handler import detect_chords
from sovits_service.sovits_handler import run_sovits
from librosa_service.librosa_handler import analyze_audio_with_librosa
from musicgen_service.musicgen_handler import generate_music

# Persona system
from persona_service.persona_analyzer import analyze_persona_audio
from persona_service.persona_cache import cache_persona, load_persona

# Advanced features
from versioning_service.version_handler import save_version, get_versions
from cover_art_service.cover_art_handler import generate_cover
from lyrics_service.lyrics_handler import generate_lyrics
from doubler_service.doubler_handler import vocal_doubler
from analog_master_service.analog_master_handler import analog_master
from automix_service.automix_handler import auto_mix
from songwriting_service.songwriting_handler import songwriting_helper
from melody_midi_service.melody_midi_handler import voice_to_midi
from ghost_mode_service.ghost_mode_handler import apply_ghost_mode


app = Flask(__name__)

# ------------------------ CORS FOR BASE44 ------------------------
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


# ------------------------ HEALTH ------------------------
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

# ------------------------ DEMUCS ------------------------
@app.post("/demucs/separate")
def demucs_route():
    audio_url = request.json.get("audio_url")
    return run_demucs(audio_url)


# ------------------------ FFMPEG ------------------------
@app.post("/ffmpeg/assemble")
def ffmpeg_route():
    tracks = request.json.get("tracks")
    return run_ffmpeg_mix(tracks)


# ------------------------ MASTERING ------------------------
@app.post("/mastering/loudness")
def mastering_route():
    audio_url = request.json.get("audio_url")
    return run_mastering(audio_url)


# ------------------------ MELODY ------------------------
@app.post("/melody/extract")
def melody_route():
    audio_url = request.json.get("audio_url")
    return extract_melody(audio_url)


# ------------------------ CHORDS ------------------------
@app.post("/chord/detect")
def chord_route():
    audio_url = request.json.get("audio_url")
    return detect_chords(audio_url)


# ================================================================
#                   UNIVERSAL DSP (LIBROSA)
# ================================================================
@app.post("/dsp/analyze")
def dsp_route():
    audio_bytes = request.data
    return analyze_audio_with_librosa(audio_bytes)


# ================================================================
#               MUSIC GENERATION (MUSICGEN)
# ================================================================
@app.post("/gen/instrumental")
def gen_instrumental():
    data = request.json
    prompt = data.get("prompt")
    duration = data.get("duration", 32)
    bpm = data.get("bpm", None)
    seed = data.get("seed", None)
    result = generate_music(prompt, duration, bpm, seed)
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

    result = generate_music(prompt, duration, bpm)
    return jsonify(result)


# ================================================================
#                     PERSONA SYSTEM
# ================================================================
@app.post("/persona/analyze")
def analyze_persona_route():
    audio_bytes = request.data
    result = analyze_persona_audio(audio_bytes)
    return jsonify(result)


@app.post("/persona/cache")
def cache_persona_route():
    payload = request.json
    persona_id = payload["persona_id"]
    persona_data = payload["persona_data"]
    return jsonify(cache_persona(persona_id, persona_data))

@app.post("/persona/preview")
def preview_persona_route():
    payload = request.json
    persona_id = payload["persona_id"]
    text = payload["text"]

    audio_data = preview_voice(persona_id, text)

    return app.response_class(
        response=audio_data,
        mimetype="audio/wav",
        status=200
    )



# ================================================================
#                     SOVITS — PERSONA SINGING
# ================================================================
@app.post("/sovits/sing")
def sovits_route():
    lyrics = request.json.get("lyrics")
    melody_midi = request.json.get("melody_midi")
    persona_id = request.json.get("persona_id")

    persona = load_persona(persona_id)

    return run_sovits(lyrics, melody_midi, persona)


# ================================================================
#                    ADVANCED FEATURES
# ================================================================

# -------- SONG VERSIONING --------
@app.post("/versions/save")
def save_version_route():
    song_id = request.json["song_id"]
    audio_url = request.json["audio_url"]
    return jsonify(save_version(song_id, audio_url))


@app.get("/versions/list")
def list_versions_route():
    song_id = request.args.get("song_id")
    return jsonify(get_versions(song_id))


# -------- COVER ART GENERATOR --------
@app.post("/cover/generate")
def cover_route():
    prompt = request.json["prompt"]
    return jsonify(generate_cover(prompt))


# -------- LYRICS GENERATOR --------
@app.post("/lyrics/generate")
def lyrics_route():
    req = request.json
    return jsonify(generate_lyrics(req["style"], req["emotion"]))


# -------- VOCAL DOUBLER --------
@app.post("/vocal/doubler")
def doubler_route():
    return vocal_doubler(request.data)


# -------- ANALOG MASTER --------
@app.post("/master/analog")
def analog_route():
    return analog_master(request.data)


# -------- AUTOMIX --------
@app.post("/automix")
def automix_route():
    stems = request.json["stems"]
    return auto_mix(stems)


# -------- SONGWRITING --------
@app.post("/songwriting")
def songwriting_route():
    return jsonify(songwriting_helper(request.json["style"]))


# -------- MELODY TO MIDI --------
@app.post("/melody/midi")
def midi_route():
    return voice_to_midi(request.data)


# -------- GHOST MODE 2.0 --------
@app.post("/vocal/ghost2")
def ghost2_route():
    return apply_ghost_mode(request.data)


# ================================================================
#                       ENTRYPOINT
# ================================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
