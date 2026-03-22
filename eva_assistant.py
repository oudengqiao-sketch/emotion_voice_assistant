import os
import re
import time
from pathlib import Path

from llama_cpp import Llama
from faster_whisper import WhisperModel
from TTS.api import TTS

from record_audio import record_audio
from emotion.audio_emotion import AudioEmotionRecognizer
from emotion.text_emotion import TextEmotionRecognizer
from emotion.emotion_fusion import EmotionFusion


# =========================
# 路径配置
# =========================
ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "llama.cpp" / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"
OUTPUT_WAV = ROOT / "output.wav"

EMOTION_VOICE = {
    "happy": ROOT / "emotion_audio" / "happy.wav",
    "sad": ROOT / "emotion_audio" / "sad.wav",
    "angry": ROOT / "emotion_audio" / "angry.wav",
    "neutral": ROOT / "emotion_audio" / "neutral.wav",
    "fear": ROOT / "emotion_audio" / "afraid.wav",
    "fearful": ROOT / "emotion_audio" / "afraid.wav",
    "afraid": ROOT / "emotion_audio" / "afraid.wav",
    "calm": ROOT / "emotion_audio" / "neutral.wav",
    "comfort": ROOT / "emotion_audio" / "neutral.wav",
    "confused": ROOT / "emotion_audio" / "neutral.wav",
}

# =========================
# 1 ASR
# =========================
print("🚀 Loading ASR...")
asr_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8",
)

# =========================
# 2 Emotion modules
# =========================
print("🚀 Loading emotion models...")
audio_emotion = AudioEmotionRecognizer()
text_emotion = TextEmotionRecognizer()
emotion_fusion = EmotionFusion()

# =========================
# 3 LLM
# =========================
print("🚀 Loading LLM...")
llm = Llama(
    model_path=str(MODEL_PATH),
    n_gpu_layers=-1,   # M1 Metal
    n_ctx=1024,
    n_threads=8,
    verbose=False,
)

# =========================
# 4 TTS
# =========================
print("🚀 Loading TTS...")
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
print("✅ All models loaded.")


# =========================
# 工具函数
# =========================
def normalize_emotion(emotion: str) -> str:
    if not emotion:
        return "neutral"

    mapping = {
        "joy": "happy",
        "joyful": "happy",
        "excited": "happy",
        "surprise": "happy",
        "surprised": "happy",

        "sadness": "sad",
        "sorrow": "sad",

        "anger": "angry",
        "ang": "angry",

        "fear": "fear",
        "fearful": "fear",
        "afraid": "fear",

        "confusion": "confused",
        "puzzled": "confused",

        "calm": "neutral",
        "comfort": "neutral",
    }

    e = emotion.strip().lower()
    return mapping.get(e, e if e in {"happy", "sad", "angry", "neutral", "fear", "confused"} else "neutral")


def get_voice_file(emotion: str):
    emotion = normalize_emotion(emotion)
    voice = EMOTION_VOICE.get(emotion)

    if voice and voice.exists():
        return str(voice)

    fallback = EMOTION_VOICE["neutral"]
    if fallback.exists():
        print(f"⚠️ 找不到情绪音色 {emotion}，使用 neutral fallback: {fallback}")
        return str(fallback)

    print("⚠️ 连 fallback 音色都不存在，将尝试使用 TTS 默认音色。")
    return None


def run_llm(user_text: str, emotion: str) -> str:
    emotion = normalize_emotion(emotion)

    prompt = f"""你是一个中文情绪语音助手。

用户当前情绪：{emotion}

要求：
1. 只用中文回答
2. 只回复一句话
3. 不要重复，不要解释，不要提“用户说”
4. 第一段必须严格输出格式：[emotion=happy|sad|angry|neutral|fear|confused]
5. 第二段直接输出回复内容
6. 不要输出多余标签，不要输出 emotion=angry 这种裸文本

用户输入：{user_text}
请开始回答：
"""

    output = llm(
        prompt,
        max_tokens=20,
        temperature=0.5,
        stop=["\n", "用户输入：", "请开始回答："]
    )

    return output["choices"][0]["text"].strip()


def parse_llm(text: str):
    # 先抓合法标签
    match = re.search(r"\[emotion=(happy|sad|angry|neutral|fear|confused)\]", text)

    if match:
        emotion = match.group(1)
    else:
        emotion = "neutral"

    # 去掉各种脏前缀
    clean_text = re.sub(r"\[emotion=.*?\]", "", text)
    clean_text = re.sub(r"emotion\s*=\s*\w+", "", clean_text, flags=re.IGNORECASE)
    clean_text = clean_text.replace("用户说的很对，", "")
    clean_text = clean_text.replace("用户说：", "")
    clean_text = clean_text.strip(" ：:，,。.!！?？")

    # 只保留第一句
    parts = re.split(r"[。！？!?]", clean_text)
    clean_text = parts[0].strip() if parts and parts[0].strip() else "嗯，我明白了。"

    # 补句号
    if not clean_text.endswith("。"):
        clean_text += "。"

    return emotion, clean_text


def speech_to_text(audio_file: str) -> str:
    segments, _ = asr_model.transcribe(audio_file)
    return "".join(seg.text for seg in segments).strip()


def play_audio(path: Path):
    if path.exists():
        os.system(f'afplay "{path}"')
    else:
        print(f"⚠️ 播放失败，文件不存在: {path}")


def speak(reply: str, emotion: str):
    voice = get_voice_file(emotion)

    if OUTPUT_WAV.exists():
        OUTPUT_WAV.unlink()

    t0 = time.time()

    if voice is not None:
        tts.tts_to_file(
            text=reply,
            speaker_wav=voice,
            language="zh",
            file_path=str(OUTPUT_WAV)
        )
    else:
        tts.tts_to_file(
            text=reply,
            language="zh",
            file_path=str(OUTPUT_WAV)
        )

    dt = time.time() - t0
    print(f"🎧 语音已生成: {OUTPUT_WAV} ({dt:.2f}s)")
    play_audio(OUTPUT_WAV)


# =========================
# 主流程
# =========================
def run_assistant():
    while True:
        try:
            audio_file = record_audio()
            user_text = speech_to_text(audio_file)

            if not user_text.strip():
                print("⚠️ 没识别到语音")
                continue

            print("📝 用户:", user_text)

            audio_e = normalize_emotion(audio_emotion.predict_emotion(audio_file))
            text_e = normalize_emotion(text_emotion.predict_emotion(user_text))
            final_e = normalize_emotion(emotion_fusion.fuse(audio_e, text_e))

            print("🎧 Audio Emotion:", audio_e)
            print("📄 Text Emotion:", text_e)
            print("🎯 Final Emotion:", final_e)

            llm_output = run_llm(user_text, final_e)
            print("🧠 LLM:", llm_output)

            reply_emotion, reply = parse_llm(llm_output)
            print("🎭 Reply Emotion:", reply_emotion)
            print("🤖 回复:", reply)

            speak(reply, reply_emotion)

        except KeyboardInterrupt:
            print("\n👋 已退出语音助手")
            break
        except Exception as e:
            print(f"❌ 本轮执行失败: {e}")
            continue


if __name__ == "__main__":
    run_assistant()