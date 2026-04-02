import os
import re
import time
from pathlib import Path

from llama_cpp import Llama
from faster_whisper import WhisperModel
from TTS.api import TTS

from agent.agent_brain import run_agent
from record_audio import record_audio
from emotion.audio_emotion import AudioEmotionRecognizer
from emotion.text_emotion import TextEmotionRecognizer
from emotion.emotion_fusion import EmotionFusion
from memory.memory_manager import MemoryManager
from tools.registry import ToolRegistry
from tools.get_time import get_time
from tools.get_weather import get_weather
from tools.save_journal import save_journal
from tools.emotion_checkin import emotion_checkin


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
    n_gpu_layers=-1,
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
# 5 Memory
# =========================
memory_manager = MemoryManager(ROOT)
print("🧠 Memory ready.")

# =========================
# 6 Tools
# =========================
registry = ToolRegistry()
registry.register("get_time", get_time)
registry.register("get_weather", get_weather)
registry.register("save_journal", save_journal)
registry.register("emotion_checkin", emotion_checkin)
print("🛠️ Tools ready.")


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


def decide_tool(user_text: str):
    if "时间" in user_text or "几点" in user_text:
        return "get_time"
    if "天气" in user_text:
        return "get_weather"
    if "记录" in user_text or "日记" in user_text:
        return "save_journal"
    if "心情" in user_text:
        return "emotion_checkin"
    return None


def call_tool(tool_name: str | None, user_text: str, emotion: str):
    if not tool_name:
        return ""

    if tool_name == "save_journal":
        return registry.call(tool_name, user_text=user_text, root_dir=str(ROOT))

    if tool_name == "emotion_checkin":
        return registry.call(tool_name, emotion=emotion, memory_manager=memory_manager)

    return registry.call(tool_name)


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


def parse_llm(text: str):
    match = re.search(r"\[emotion=(happy|sad|angry|neutral|fear|confused)\]", text)

    if match:
        emotion = match.group(1)
    else:
        emotion = "neutral"

    clean_text = re.sub(r"\[emotion=.*?\]", "", text)
    clean_text = re.sub(r"emotion\s*=\s*\w+", "", clean_text, flags=re.IGNORECASE)
    clean_text = clean_text.replace("用户说的很对，", "")
    clean_text = clean_text.replace("用户说：", "")
    clean_text = clean_text.strip(" ：:，,。.!！?？")

    parts = re.split(r"[。！？!?]", clean_text)
    clean_text = parts[0].strip() if parts and parts[0].strip() else "嗯，我明白了。"

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

            agent_result = run_agent(
                user_text=user_text,
                emotion=final_e,
                memory_manager=memory_manager,
                llm=llm,
                decide_tool=decide_tool,
                call_tool=call_tool,
            )

            if agent_result["tool_name"]:
                print("🛠️ Tool:", agent_result["tool_name"])
                print("🛠️ Tool Result:", agent_result["tool_result"])

            print("🧠 Emotion Trend:", agent_result["memory_context"]["emotion_trend"])
            print("🧠 LLM:", agent_result["llm_output"])

            reply_emotion, reply = parse_llm(agent_result["llm_output"])
            print("🎭 Reply Emotion:", reply_emotion)
            print("🤖 回复:", reply)

            memory_manager.save_turn(
                user_text=user_text,
                assistant_reply=reply,
                emotion=final_e,
            )

            speak(reply, reply_emotion)

        except KeyboardInterrupt:
            print("\n👋 已退出语音助手")
            break
        except Exception as e:
            print(f"❌ 本轮执行失败: {e}")
            continue


if __name__ == "__main__":
    run_assistant()
