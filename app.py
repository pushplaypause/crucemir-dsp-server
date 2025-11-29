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
            "/dsp/analyze"  # librosa version of DSP analysis
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
    audio_url = request.json.get("audio_url")
    return analyze_audio_with_librosa(audio_url)

# ---------------------------------
# ENTRYPOINT FOR GUNICORN
# ---------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
