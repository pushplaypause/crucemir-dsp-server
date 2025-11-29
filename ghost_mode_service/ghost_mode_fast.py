import tempfile
import requests
import subprocess

def ghost_mode_fast(audio_url):
    """
    Fast CPU-safe Ghost Mode (default).
    """
    input_path = tempfile.mktemp(suffix=".wav")
    out_path = tempfile.mktemp(suffix=".wav")

    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af",
        "asetrate=44100*0.9,"
        "atempo=1/0.9,"
        "highpass=f=300,"
        "aecho=0.8:0.9:80:0.7",
        out_path
    ]

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with open(out_path, "rb") as f:
        return f.read()
