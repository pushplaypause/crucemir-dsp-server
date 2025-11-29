from flask import Flask, request, jsonify

# Import handlers
from demucs.demucs_handler import run_demucs
from ffmpeg.ffmpeg_handler import run_ffmpeg_mix
from mastering.mastering_handler import run_mastering
from melody.melody_handler import extract_melody
from chord.chord_handler import detect_chords
from openvoice_service.openvoice_handler import run_openvoice
from sovits.sovits_handler import run_sovits
from essentia.essentia_handler import run_essentia

app = Flask(__name__)

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
            "/essentia/analyze"
        ]
    })

# DEMUCS STEM SEPARATION
@app.post("/demucs/separate")
def demucs_route():
    audio_url = request.json["audio_url"]
    return run_demucs(audio_url)

# FFMPEG MIXING / ASSEMBLY
@app.post("/ffmpeg/assemble")
def ffmpeg_route():
    tracks = request.json["tracks"]
    return run_ffmpeg_mix(tracks)

# MASTERING SERVICE
@app.post("/mastering/loudness")
def mastering_route():
    audio_url = request.json["audio_url"]
    return run_mastering(audio_url)

# MELODY EXTRACTION
@app.post("/melody/extract")
def melody_route():
    audio_url = request.json["audio_url"]
    return extract_melody(audio_url)

# CHORD DETECTION
@app.post("/chord/detect")
def chord_route():
    audio_url = request.json["audio_url"]
    return detect_chords(audio_url)

# OPENVOICE (Vale character TTS)
@app.post("/openvoice/say")
def openvoice_route():
    text = request.json["text"]
    return run_openvoice(text)

# SOVITS (Vale singing)
@app.post("/sovits/sing")
def sovits_route():
    lyrics = request.json["lyrics"]
    melody_midi = request.json["melody_midi"]
    return run_sovits(lyrics, melody_midi)

# ESSENTIA DSP ANALYSIS
@app.post("/essentia/analyze")
def essentia_route():
    return run_essentia(request.data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
