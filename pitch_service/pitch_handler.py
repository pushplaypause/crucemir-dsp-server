import tempfile
import subprocess
import requests

def pitch_shift(audio_url, semitones):
    input_path = tempfile.mktemp(suffix=".wav")
    output_path = tempfile.mktemp(suffix=".wav")

    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    # Rubberband pitch shifting
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af", f"rubberband=pitch={2 ** (semitones/12)}",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with open(output_path, "rb") as f:
        return f.read()
