from asr.whisper_asr import WhisperASR

asr = WhisperASR()

audio_file = "test.wav"

text = asr.transcribe(audio_file)

print("Recognized text:", text)
