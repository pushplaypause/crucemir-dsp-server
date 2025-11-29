import requests
import tempfile
import base64
import os

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

MODEL_ID = "meta/musicgen-large"   # Replicate MusicGen Large

def generate_music(prompt: str, duration: int = 32, bpm: int = None, seed: int = None):
    """
    Generates an instrumental audio clip using Replicate's MusicGen-Large model.
    """

    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
        "duration": duration,  # seconds
        "seed": seed
    }

    if bpm:
        payload["bpm"] = bpm

    response = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers=headers,
        json={
            "version": MODEL_ID,
            "input": payload
        }
    )

    prediction = response.json()

    # Wait for completion
    prediction_url = prediction["urls"]["get"]

    while True:
        poll = requests.get(prediction_url, headers=headers).json()
        if poll["status"] in ["succeeded", "failed", "canceled"]:
            break

    if poll["status"] != "succeeded":
        return {"status": "error", "message": poll}

    output_url = poll["output"][0]

    # download MP3
    audio_bytes = requests.get(output_url).content
    encoded_audio = base64.b64encode(audio_bytes).decode()

    return {
        "status": "ok",
        "prompt": prompt,
        "duration": duration,
        "audio_url": output_url,
        "audio_base64": encoded_audio
    }
