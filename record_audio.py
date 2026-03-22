import sounddevice as sd
import numpy as np
import wave

def record_audio(filename="input.wav", duration=4, fs=16000):

    print("🎤 请说话...")

    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    audio = (audio * 32767).astype(np.int16)

    with wave.open(filename, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(fs)
        f.writeframes(audio.tobytes())

    return filename