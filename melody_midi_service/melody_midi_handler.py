import librosa
import tempfile
from mido import Message, MidiFile, MidiTrack

def voice_to_midi(audio_bytes):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(audio_bytes)
    tmp.close()

    y, sr = librosa.load(tmp.name, sr=44100)

    f0 = librosa.yin(y, 50, 1500, sr=sr)

    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)

    for freq in f0:
        if freq > 0:
            note = int(librosa.hz_to_midi(freq))
            track.append(Message('note_on', note=note, velocity=80, time=120))

    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mid").name
    midi.save(out_path)

    return open(out_path, "rb").read()
