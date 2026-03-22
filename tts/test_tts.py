from TTS.api import TTS

tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

tts.tts_to_file(
    text="我会陪着你，一切都会好起来的。",
    speaker_wav="../emotion_audio/sad.wav",
    language="zh",
    file_path="output.wav"
)

print("语音已生成 output.wav")