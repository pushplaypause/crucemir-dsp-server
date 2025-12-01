# generate_dummy_ir.py

import soundfile as sf
import numpy as np
import os

os.makedirs("impulse_responses", exist_ok=True)

names = ["cinematic", "ghost", "frozen", "glassroom", "cathedral"]

for name in names:
    ir = np.random.randn(44100).astype(np.float32) * 0.001
    sf.write(f"impulse_responses/{name}.wav", ir, 44100)

print("Dummy IRs generated.")
