import subprocess
import tempfile
import os
from flask import jsonify

def preview_voice(text, voice_model="default"):
    """
    Uses OpenVoice CLI to generate a temporary preview voice file.
    """
    try:
        tmp_dir = tempfile.mkdtemp()
        out_path = os.path.join(tmp_dir, "preview.wav")

        # OpenVoice CLI command
        cmd = [
            "openvoice",
            "--text", text,
            "--output", out_path,
            "--voice", voice_model
        ]

        subprocess.run(cmd, check=True)

        return jsonify({
            "success": True,
            "preview_url": out_path
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })