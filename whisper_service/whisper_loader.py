from faster_whisper import WhisperModel

# Global model instance (loads once)
model = WhisperModel(
    "medium",
    device="cpu",
    compute_type="int8",   # ✔ ENABLE INT8 QUANTIZATION
    cpu_threads=4,         # Adjust based on your Render plan
    num_workers=1
)

def transcribe(audio_path):
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True
    )
    return list(segments), info
