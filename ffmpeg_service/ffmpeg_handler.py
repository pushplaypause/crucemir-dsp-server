import tempfile
import subprocess
import os
import requests
import uuid
import zipfile


# ============================================================
#  MIX MULTIPLE STEMS
# ============================================================
def run_ffmpeg_mix(tracks):
    """
    tracks = [
        { "url": "https://...", "volume": 1.0 },
        ...
    ]
    Returns: raw WAV bytes
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        inputs = []
        filter_parts = []

        # Download stems
        for i, track in enumerate(tracks):
            path = os.path.join(tmpdir, f"track{i}.wav")
            audio = requests.get(track["url"]).content
            with open(path, "wb") as f:
                f.write(audio)

            volume = track.get("volume", 1.0)

            inputs.extend(["-i", path])
            filter_parts.append(f"[{i}:a]volume={volume}[a{i}]")

        # Build ffmpeg mix filter
        mix_inputs = "".join(f"[a{i}]" for i in range(len(tracks)))
        filter_complex = (
            ";".join(filter_parts)
            + f";{mix_inputs}amix=inputs={len(tracks)}:normalize=0[out]"
        )

        output_path = os.path.join(tmpdir, "mix.wav")

        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]", output_path
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # Return bytes, not a JSON
        with open(output_path, "rb") as f:
            return f.read()


# ============================================================
#  ZIP EXPORTED STEMS
# ============================================================
def create_zip_from_stems(stems):
    """
    stems = [
        { "name": "vocal", "url": "https://..." },
        { "name": "drums", "url": "https://..." },
        ...
    ]
    Returns: path to .zip file in /tmp/
    """

    zip_filename = f"stems_{uuid.uuid4().hex}.zip"
    zip_path = os.path.join("/tmp", zip_filename)

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for stem in stems:
            name = stem["name"] + ".wav"

            audio = requests.get(stem["url"]).content
            temp_path = tempfile.mktemp(suffix=".wav")

            with open(temp_path, "wb") as f:
                f.write(audio)

            zipf.write(temp_path, arcname=name)

    return zip_path
