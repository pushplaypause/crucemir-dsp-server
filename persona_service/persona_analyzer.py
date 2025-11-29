# persona_service/persona_analyzer.py

import librosa
import numpy as np
import io

def analyze_persona_audio(audio_bytes):
    try:
        audio_np, sr = librosa.load(io.BytesIO(audio_bytes), sr=44100)

        # Pitch analysis
        pitches, magnitudes = librosa.piptrack(y=audio_np, sr=sr)
        pitch_values = pitches[magnitudes > np.median(magnitudes)]
        pitch_min = float(np.percentile(pitch_values, 5)) if len(pitch_values) else 80
        pitch_max = float(np.percentile(pitch_values, 95)) if len(pitch_values) else 240

        # Timbre (MFCC mean vector)
        mfcc = librosa.feature.mfcc(y=audio_np, sr=sr, n_mfcc=20)
        timbre_vector = np.mean(mfcc, axis=1).tolist()

        # Breathiness (HNR estimate)
        S = np.abs(librosa.stft(audio_np))
        harmonic, percussive = librosa.decompose.hpss(S)
        breathiness = float(np.mean(percussive) / (np.mean(harmonic) + 1e-6))

        # Grit (spectral flatness)
        grit = float(np.mean(librosa.feature.spectral_flatness(y=audio_np)))

        return {
            "pitch_range": [pitch_min, pitch_max],
            "timbre_vector": timbre_vector,
            "breathiness": breathiness,
            "grit": grit,
            "emotion_curve": timbre_vector[:5]
        }

    except Exception as e:
        return {"error": str(e)}
