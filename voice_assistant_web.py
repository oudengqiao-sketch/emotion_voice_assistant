import base64
import os
import shutil
import subprocess
import tempfile
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from faster_whisper import WhisperModel
from llama_cpp import Llama
from TTS.api import TTS

from emotion.audio_emotion import AudioEmotionRecognizer
from emotion.text_emotion import TextEmotionRecognizer
from emotion.emotion_fusion import EmotionFusion


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "web_static"
TEMP_DIR = Path(os.getenv("EVA_TEMP_DIR", ROOT / "web_tmp"))
MODEL_PATH = Path(
    os.getenv(
        "EVA_MODEL_PATH",
        ROOT / "llama.cpp" / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf",
    )
)
WHISPER_MODEL_NAME = os.getenv("EVA_WHISPER_MODEL", "base")
TTS_MODEL_NAME = os.getenv("EVA_TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
LLM_THREADS = int(os.getenv("EVA_LLM_THREADS", "8"))
LLM_CONTEXT = int(os.getenv("EVA_LLM_CONTEXT", "1024"))
LLM_GPU_LAYERS = int(os.getenv("EVA_LLM_GPU_LAYERS", "-1"))

TEMP_DIR.mkdir(exist_ok=True)

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

    value = emotion.strip().lower()
    allowed = {"happy", "sad", "angry", "neutral", "fear", "confused"}
    return mapping.get(value, value if value in allowed else "neutral")


def get_voice_file(emotion: str):
    voice = EMOTION_VOICE.get(normalize_emotion(emotion))
    if voice and voice.exists():
        return str(voice.resolve())

    fallback = EMOTION_VOICE["neutral"]
    return str(fallback.resolve()) if fallback.exists() else None


def build_prompt(user_text: str, emotion: str) -> str:
    return f"""你是一个中文情绪语音助手。

用户当前情绪：{emotion}

要求：
1. 只用中文回答
2. 只回复一句话
3. 回复长度控制在10到18个字左右
4. 不要重复，不要解释，不要提“用户说”
5. 语气自然，适合网页实时语音体验
6. 只输出回复内容，不要输出标签

用户输入：{user_text}
回复："""


def parse_llm_reply(text: str) -> str:
    clean_text = text.strip().replace("回复：", "")
    clean_text = clean_text.strip(" ：:，,。.!！?？")
    parts = [part.strip() for part in clean_text.replace("\n", " ").split("。") if part.strip()]
    clean_text = parts[0] if parts else "嗯，我明白了"
    if not clean_text.endswith("。"):
        clean_text += "。"
    return clean_text


class AssistantService:
    def __init__(self):
        self._loaded = False
        self._load_error = ""
        self._lock = threading.Lock()
        self.asr_model = None
        self.audio_emotion = None
        self.text_emotion = None
        self.emotion_fusion = None
        self.llm = None
        self.tts = None

    @property
    def ready(self) -> bool:
        return self._loaded and not self._load_error

    def load_models(self):
        try:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(f"缺少 LLM 模型文件: {MODEL_PATH}")

            print("🚀 Loading ASR...")
            self.asr_model = WhisperModel(WHISPER_MODEL_NAME, device="cpu", compute_type="int8")

            print("🚀 Loading emotion models...")
            self.audio_emotion = AudioEmotionRecognizer()
            self.text_emotion = TextEmotionRecognizer()
            self.emotion_fusion = EmotionFusion()

            print("🚀 Loading LLM...")
            self.llm = Llama(
                model_path=str(MODEL_PATH),
                n_gpu_layers=LLM_GPU_LAYERS,
                n_ctx=LLM_CONTEXT,
                n_threads=LLM_THREADS,
                verbose=False,
            )

            print("🚀 Loading TTS...")
            self.tts = TTS(model_name=TTS_MODEL_NAME)
            self.tts.to("cpu")

            self._loaded = True
            self._load_error = ""
            print("✅ Web models loaded.")
        except Exception as exc:
            self._loaded = False
            self._load_error = str(exc)
            print(f"❌ Model startup failed: {exc}")

    def ffmpeg_normalize(self, input_path: Path) -> Path:
        normalized_path = TEMP_DIR / f"normalized_{int(time.time() * 1000)}.wav"
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-ar",
            "16000",
            "-ac",
            "1",
            str(normalized_path),
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise RuntimeError("服务器缺少 ffmpeg，无法处理浏览器录音文件。") from exc
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.strip() or "ffmpeg 转码失败"
            raise RuntimeError(detail) from exc

        return normalized_path

    def speech_to_text(self, audio_path: Path) -> str:
        segments, _ = self.asr_model.transcribe(str(audio_path))
        return "".join(seg.text for seg in segments).strip()

    def run_llm(self, user_text: str, emotion: str) -> str:
        prompt = build_prompt(user_text, normalize_emotion(emotion))
        output = self.llm(
            prompt,
            max_tokens=18,
            temperature=0.5,
            stop=["\n", "用户输入：", "回复："],
        )
        return output["choices"][0]["text"].strip()

    def synthesize(self, reply: str, emotion: str, output_path: Path):
        voice = get_voice_file(emotion)
        if output_path.exists():
            output_path.unlink()

        kwargs = {
            "text": reply,
            "language": "zh",
            "file_path": str(output_path),
        }
        if voice is not None:
            kwargs["speaker_wav"] = voice
        self.tts.tts_to_file(**kwargs)

    def analyze(self, input_path: Path):
        if not self.ready:
            raise RuntimeError(self._load_error or "模型尚未准备完成")

        started_at = time.time()
        normalized_path = self.ffmpeg_normalize(input_path)
        output_path = TEMP_DIR / f"reply_{int(time.time() * 1000)}.wav"

        try:
            with self._lock:
                user_text = self.speech_to_text(normalized_path)
                if not user_text.strip():
                    raise ValueError("未识别到语音")

                audio_e = normalize_emotion(
                    self.audio_emotion.predict_emotion(str(normalized_path))
                )
                text_e = normalize_emotion(self.text_emotion.predict_emotion(user_text))
                final_e = normalize_emotion(self.emotion_fusion.fuse(audio_e, text_e))

                reply = parse_llm_reply(self.run_llm(user_text, final_e))
                reply_emotion = final_e
                self.synthesize(reply, reply_emotion, output_path)

            with open(output_path, "rb") as file_obj:
                audio_base64 = base64.b64encode(file_obj.read()).decode("utf-8")

            return {
                "user_text": user_text,
                "audio_emotion": audio_e,
                "text_emotion": text_e,
                "final_emotion": final_e,
                "reply": reply,
                "reply_emotion": reply_emotion,
                "elapsed_sec": round(time.time() - started_at, 2),
                "audio_base64": audio_base64,
            }
        finally:
            for path in (normalized_path, output_path):
                try:
                    if path.exists():
                        path.unlink()
                except Exception:
                    pass


service = AssistantService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    service.load_models()
    yield


app = FastAPI(
    title="Emotion Voice Assistant",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    if service.ready:
        return {"status": "ready"}
    return {
        "status": "starting",
        "detail": service._load_error or "模型加载中",
    }


@app.post("/api/analyze")
async def analyze(request: Request, file: UploadFile = File(...)):
    suffix = Path(file.filename or "recording.webm").suffix or ".webm"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=TEMP_DIR) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        input_path = Path(temp_file.name)

    try:
        return service.analyze(input_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            if input_path.exists():
                input_path.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
