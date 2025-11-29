import subprocess
import uuid
import os

def run_openvoice(text, voice="default"):
    """
    Runs OpenVoice via the CLI version installed from `openvoice-cli`
    and returns the path to the generated TTS audio file.
    """

    # Output file
    output_path = f"/tmp/{uuid.uuid4()}.wav"

    # CLI command
    cmd = [
        "openvoice",     # CLI binary
        "--text", text,
        "--voice", voice,
        "--output", output_path
    ]

    # Execute OpenVoice
    subprocess.run(cmd, check=True)

    return output_path
