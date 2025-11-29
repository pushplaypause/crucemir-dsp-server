from flask import Flask, request, jsonify
from flask_cors import CORS

# Import microservice handlers
from demucs_service.demucs_handler import run_demucs
from ffmpeg_service.ffmpeg_handler import run_ffmpeg_mix
from mastering_service.mastering_handler import run_mastering
from melody_service.melody_handler import extract_melody
from chord_service.chord_handler import detect_chords
from openvoice_service.openvoice_handler import run_openvoice
from sovits_service.sovits_handler import run_sovits
from librosa_service.librosa_handler import analyze_audio_with_librosa
from musicgen_service.musicgen_handler import generate_music
from persona_service.persona_analyzer import analyze_persona_audio
from persona_service.persona_cache import cache_persona, load_persona
from persona_service.persona_preview import preview_voice

app = Flask(__name__)

# ---------------------------------
# 🔥 ENABLE CORS FOR BASE44 ACCESS
# ---------------------------------
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

# ---------------------------------
# 🔥 ALLOW OPTIONS PREFLIGHT REQUESTS
# ---------------------------------
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        return "", 200

# ---------------------------------
# HEALTH CHECK ENDPOINT
# ---------------------------------
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
            "/openvoice/say",
            "/sovits/sing",
            "/dsp/analyze"
        ]
    })

# ---------------------------------
# 🎵 DEMUCS STEM SEPARATION
# ---------------------------------
@app.post("/demucs/separate")
def demucs_route():
    audio_url = request.json.get("audio_url")
    return run_demucs(audio_url)

# ---------------------------------
# 🎛️ FFMPEG MIXING & STEM ASSEMBLY
# ---------------------------------
@app.post("/ffmpeg/assemble")
def ffmpeg_route():
    tracks = request.json.get("tracks")
    return run_ffmpeg_mix(tracks)

# ---------------------------------
# 🔊 MASTERING (LOUDNESS)
# ---------------------------------
@app.post("/mastering/loudness")
def mastering_route():
    audio_url = request.json.get("audio_url")
    return run_mastering(audio_url)

# ---------------------------------
# 🎼 MELODY EXTRACTION
# ---------------------------------
@app.post("/melody/extract")
def melody_route():
    audio_url = request.json.get("audio_url")
    return extract_melody(audio_url)

# ---------------------------------
# 🎸 CHORD DETECTION
# ---------------------------------
@app.post("/chord/detect")
def chord_route():
    audio_url = request.json.get("audio_url")
    return detect_chords(audio_url)

# ---------------------------------
# 🗣️ OPENVOICE — Vale TTS
# ---------------------------------
@app.post("/openvoice/say")
def openvoice_route():
    text = request.json.get("text")
    return run_openvoice(text)

# ---------------------------------
# 🗣️ GENERATE INSTRUMENTAL
# ---------------------------------
@app.post("/gen/instrumental")
def gen_instrumental():
    data = request.json

    prompt = data.get("prompt")
    duration = data.get("duration", 32)
    bpm = data.get("bpm", None)
    seed = data.get("seed", None)

    result = generate_music(prompt, duration, bpm, seed)
    return jsonify(result)

# ---------------------------------
# 🔥 Analyze voice audio for persona creation
# ---------------------------------
@app.post("/persona/analyze")
def analyze_persona_route():
    audio_bytes = request.data
    result = analyze_persona_audio(audio_bytes)
    return jsonify(result)

# ---------------------------------
# 🔥 Cache persona in Render
# ---------------------------------
@app.post("/persona/cache")
def cache_persona_route():
    payload = request.json
    persona_id = payload["persona_id"]
    persona_data = payload["persona_data"]
    return jsonify(cache_persona(persona_id, persona_data))

# ---------------------------------
# 🔥 Preview persona voice
# ---------------------------------
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

# ---------------------------------
# 🔥 Update SoVITS singing endpoint for persona conditioning
# ---------------------------------
@app.post("/sovits/sing")
def sovits_route():
    lyrics = request.json.get("lyrics")
    melody_midi = request.json.get("melody_midi")
    persona_id = request.json.get("persona_id")

    persona = load_persona(persona_id)

    return run_sovits(lyrics, melody_midi, persona)


# ---------------------------------
# 🗣️ GENERATE FULL SONG SKELETON
# ---------------------------------
@app.post("/gen/song")
def gen_song():
    data = request.json

    style = data.get("style", "cinematic metalcore")
    emotion = data.get("emotion", "dark and emotional")
    bpm = data.get("bpm", 120)
    duration = data.get("duration", 32)

    prompt = f"{style}, {emotion}, atmospheric, cinematic, metalcore, guitars, drums, ambience, cohesive composition"

    result = generate_music(prompt, duration, bpm)
    return jsonify(result)


# ---------------------------------
# 🎤 SOVITS — Vale Singing
# ---------------------------------
@app.post("/sovits/sing")
def sovits_route():
    lyrics = request.json.get("lyrics")
    melody_midi = request.json.get("melody_midi")
    return run_sovits(lyrics, melody_midi)

# ---------------------------------
# 🎚️ DSP ANALYSIS (Librosa)
# ---------------------------------
@app.post("/dsp/analyze")
def dsp_route():
    audio_bytes = request.data
    return analyze_audio_with_librosa(audio_bytes)

# ---------------------------------
# ENTRYPOINT FOR GUNICORN
# ---------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
