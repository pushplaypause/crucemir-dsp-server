import subprocess
import uuid
import tempfile

def preview_voice(text: str, voice_model="neutral"):
    tmp_output = f"/tmp/preview_{uuid.uuid4()}.wav"

    cmd = [
        "openvoice",
        "--text", text,
        "--voice", voice_model,
        "--output", tmp_output
    ]

    subprocess.run(cmd, check=True)

    return open(tmp_output, "rb").read()
