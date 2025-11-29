import tempfile, subprocess, os, base64, requests
from flask import jsonify

def run_ffmpeg_mix(tracks):
    with tempfile.TemporaryDirectory() as tmpdir:
        inputs = []
        filter_parts = []

        for i, track in enumerate(tracks):
            path = os.path.join(tmpdir, f"track{i}.wav")
            r = requests.get(track["url"])
            with open(path, "wb") as f:
                f.write(r.content)

            inputs.extend(["-i", path])
            filter_parts.append(f"[{i}:a]volume={track.get('volume',1)}[a{i}]")

        # assemble filter graph
        mix_inputs = "".join(f"[a{i}]" for i in range(len(tracks)))
        filter_complex = ";".join(filter_parts) + f";{mix_inputs}amix=inputs={len(tracks)}:normalize=0[out]"

        output_path = os.path.join(tmpdir, "mix.wav")

        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]", output_path
        ]
        subprocess.run(cmd, check=True)

        with open(output_path, "rb") as f:
            audio64 = base64.b64encode(f.read()).decode()

        return jsonify({"audio": audio64, "success": True})
