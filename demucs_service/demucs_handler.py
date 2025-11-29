import os
import tempfile
import subprocess
import requests
import uuid

def run_demucs(audio_url):
    """
    Input: audio_url
    Output: [
        { "name": "vocal", "url": "..." },
        { "name": "drums", "url": "..." },
        ...
    ]
    """

    # Download audio
    input_path = tempfile.mktemp(suffix=".wav")
    with open(input_path, "wb") as f:
        f.write(requests.get(audio_url).content)

    # Output stem folder
    prefix = uuid.uuid4().hex
    output_dir = f"/tmp/demucs_{prefix}"
    os.makedirs(output_dir, exist_ok=True)

    # Run Demucs
    cmd = [
        "python3", "-m", "demucs.separate",
        "-o", output_dir,
        input_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Path to stems
    stems_dir = os.path.join(output_dir, "htdemucs", os.path.basename(input_path).split(".")[0])

    stems = []
    for stem_file in os.listdir(stems_dir):
        if stem_file.endswith(".wav"):
            src = os.path.join(stems_dir, stem_file)
            name = stem_file.replace(".wav", "")
            dest = f"/tmp/{prefix}_{stem_file}"
            os.rename(src, dest)
            stems.append({"name": name, "path": dest})

    return stems
