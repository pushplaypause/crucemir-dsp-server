import subprocess
import uuid
import os

def run_sovits(audio_path, speaker="default"):
    output_path = f"/tmp/sovits_{uuid.uuid4()}.wav"

    cmd = [
        "sovits-cli",
        "--input", audio_path,
        "--speaker", speaker,
        "--output", output_path
    ]

    subprocess.run(cmd, check=True)

    return output_path
