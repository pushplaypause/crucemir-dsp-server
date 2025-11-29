import tempfile
import subprocess
import requests

def time_stretch(audio_url, stretch_factor):
    input_path = tempfile.mktemp(suffix=".wav")
    output_path = tempfile.mktemp(suffix=".wav")

    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af", f"atempo={stretch_factor}",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with open(output_path, "rb") as f:
        return f.read()
