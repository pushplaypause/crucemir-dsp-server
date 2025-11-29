import tempfile, os, base64, requests, subprocess
from flask import jsonify

def run_demucs(audio_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Download audio
        input_path = os.path.join(tmpdir, "input.wav")
        r = requests.get(audio_url)
        with open(input_path, "wb") as f:
            f.write(r.content)

        # Run Demucs
        output_dir = os.path.join(tmpdir, "out")
        subprocess.run([
            "python", "-m", "demucs", "-n", "htdemucs",
            "--out", output_dir, input_path
        ], check=True)

        # Locate stems
        stems_dir = os.path.join(output_dir, "htdemucs", "input")
        stems = {}

        for name in ["vocals", "drums", "bass", "other"]:
            path = os.path.join(stems_dir, f"{name}.wav")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    stems[name] = base64.b64encode(f.read()).decode()

        return jsonify({"success": True, "stems": stems})
