# test_tts.py
from TTS.api import TTS
import torch

# 🔹 正确导入 XttsConfig
from TTS.tts.configs.xtts_config import XttsConfig

# 🔹 允许加载 XttsConfig
torch.serialization.add_safe_globals([XttsConfig])

# 🔹 创建 TTS 对象（使用 xtts_v2 模型）
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

# 🔹 生成语音
tts.tts_to_file(
    text="我会陪着你，一切都会好起来的。",
    speaker_wav="../emotion_audio/sad.wav",  # 如果没有 wav，可改为 None
    language="zh",
    file_path="output.wav"
)

print("语音已生成 output.wav")