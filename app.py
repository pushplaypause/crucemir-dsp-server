from flask import Flask, request, jsonify

# Import service handlers
from demucs_service.demucs_handler import run_demucs
from ffmpeg_service.ffmpeg_handler import run_ffmpeg_mix
from mastering_service.mastering_handler import run_mastering
from melody_service.melody_handler import extract_melody
from chord_service.chord_handler import detect_chords
from openvoice_service.openvoice_handler import run_openvoice
from sovits_service.sovits_handler import run_sovits
from librosa_service.librosa_handler import analyze_audio_with_librosa

app = Flask(__name__)

# HEALTH CHECK
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

# -------------------------------------------------------
# 🌑 1. DEMUCS STEM SEPARATION
# -------------------------------------------------------
@app.post("/demucs/separate")
def demucs_route():
    audio_url = request.json.get("audio_url")
    return run_demucs(audio_url)

# -------------------------------------------------------
# 🌑 2. FFMPEG MIXING / ASSEMBLY
# -------------------------------------------------------
@app.post("/ffmpeg/assemble")
def ffmpeg_route():
    tracks = request.json.get("tracks")
    return run_ffmpeg_mix(tracks)

# -------------------------------------------------------
# 🌑 3. MASTERING SERVICE
# -------------------------------------------------------
@app.post("/mastering/loudness")
def mastering_route():
    audio_url = request.json.get("audio_url")
    return run_mastering(audio_url)

# -------------------------------------------------------
# 🌑 4. MELODY EXTRACTION
# -------------------------------------------------------
@app.post("/melody/extract")
def melody_route():
    audio_url = request.json.get("audio_url")
    return extract_melody(audio_url)

# -------------------------------------------------------
# 🌑 5. CHORD DETECTION
# -------------------------------------------------------
@app.post("/chord/detect")
def chord_route():
    audio_url = request.json.get("audio_url")
    return detect_chords(audio_url)

# -------------------------------------------------------
# 🌑 6. OPENVOICE (Vale TTS Mode)
# -------------------------------------------------------
@app.post("/openvoice/say")
def openvoice_route():
    text = request.json.get("text")
    return run_openvoice(text)

# -------------------------------------------------------
# 🌑 7. SOVITS (Vale Singing Mode)
# -------------------------------------------------------
@app.post("/sovits/sing")
def sovits_route():
    lyrics = request.json.get("lyrics")
    melody_midi = request.json.get("melody_midi")
    return run_sovits(lyrics, melody_midi)

# -------------------------------------------------------
# 🌑 8. LIBROSA DSP ANALYSIS (Replaces Essentia)
# -------------------------------------------------------
@app.post("/dsp/analyze")
def dsp_route():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    file = request.files["audio"]
    tmp_path = "/tmp/input.wav"
    file.save(tmp_path)

    result = analyze_audio_with_librosa(tmp_path)
    return jsonify({
        "status": "ok",
        "analysis": result
    })

# -------------------------------------------------------
# ENTRYPOINT (Gunicorn will override this)
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
