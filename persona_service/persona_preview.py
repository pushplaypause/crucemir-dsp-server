import subprocess
import tempfile
import os

PERSONA_DIR = "/app/personas"

def preview_voice(persona_id, text):
    """
    Generate a preview of a persona's voice using OpenVoice CLI.
    Returns raw audio bytes (WAV).
    """

    voice_path = os.path.join(PERSONA_DIR, persona_id, "voice.pt")

    if not os.path.exists(voice_path):
        return {
            "success": False,
            "error": f"No persona embedding found at {voice_path}"
        }

    tmp_dir = tempfile.mkdtemp()
    out_path = os.path.join(tmp_dir, "preview.wav")

    cmd = [
        "openvoice",
        "--text", text,
        "--voice", voice_path,
        "--output", out_path
    ]

    try:
        subprocess.run(cmd, check=True)
        with open(out_path, "rb") as f:
            audio = f.read()

        return audio

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
