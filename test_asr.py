from faster_whisper import WhisperModel

model = WhisperModel("small", device="cpu")

segments, _ = model.transcribe("test.wav")

for s in segments:
    print(s.text)