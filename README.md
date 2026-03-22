# Emotion Voice Assistant

一个中文情绪语音助手项目，整合了语音录制、语音识别、音频情绪识别、文本情绪识别、情绪融合、大语言模型回复，以及情绪化语音合成。

项目目标是让助手不仅能“听懂你说了什么”，还能尽量判断你说话时的情绪，并用更贴近情绪状态的语气回复。

现在仓库中同时包含：

- 命令行版本：`eva_assistant.py`
- 网页版 Demo：`voice_assistant_web.py`
- 可部署静态前端：`web_static/`
- Docker 启动文件：`Dockerfile`

## 功能简介

- 录制用户语音输入
- 使用 Whisper / Faster-Whisper 做语音转文字
- 基于音频信号识别说话情绪
- 基于文本内容识别情绪倾向
- 融合音频和文本情绪结果
- 使用本地 LLM 生成中文回复
- 使用 XTTS 将回复合成为语音
- 根据情绪选择不同参考音色

## 处理流程

1. 用户录音
2. ASR 将语音转成文本
3. 音频情绪模型预测语音情绪
4. 文本情绪模型预测文本情绪
5. 情绪融合模块输出最终情绪
6. LLM 生成带情绪标签的回复
7. TTS 根据情绪音色生成语音并播放

## 项目结构

```text
emotion_voice_assistant/
├── asr/
│   └── whisper_asr.py
├── emotion/
│   ├── audio_emotion.py
│   ├── emotion_fusion.py
│   └── text_emotion.py
├── tts/
│   └── test_tts.py
├── eva_assistant.py
├── voice_assistant_web.py
├── web_static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── emotion_pipeline.py
├── record_audio.py
├── requirements.txt
├── Dockerfile
├── test_asr.py
├── test_audio_emotion.py
├── test_emotion_fusion.py
├── test_pipeline.py
├── test_text_emotion.py
├── test_tts.py
└── test_whisper_asr.py
```

## 主要技术栈

- Python
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [openai-whisper](https://github.com/openai/whisper)
- [Transformers](https://github.com/huggingface/transformers)
- [PyTorch](https://pytorch.org/)
- [Coqui TTS](https://github.com/coqui-ai/TTS)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)

## 运行前准备

建议使用 Python 3.10 或 3.11，并先创建虚拟环境。

```bash
python -m venv venv
source venv/bin/activate
```

安装项目依赖：

```bash
pip install -r requirements.txt
```

如果你想手动安装，也至少需要这些核心依赖：

```bash
pip install fastapi "uvicorn[standard]" python-multipart
pip install numpy sounddevice
pip install torch torchaudio transformers
pip install openai-whisper faster-whisper
pip install TTS
pip install llama-cpp-python
```

如果你在 macOS 上运行命令行版语音播放，代码里当前使用的是 `afplay`。

## 模型与资源

当前项目代码默认依赖以下资源：

- 本地 GGUF 大模型文件  
  `llama.cpp/models/qwen2.5-3b-instruct-q4_k_m.gguf`
- 情绪参考音频目录  
  `emotion_audio/`
- Coqui XTTS 模型
- Whisper / Faster-Whisper 模型
- Hugging Face 上的情绪识别模型

注意：音频参考文件和模型文件通常比较大，本仓库目前没有上传这些资源文件，需要你在本地自行准备。

## 运行方式

启动主程序：

```bash
python eva_assistant.py
```

主程序会完成：

- 加载 ASR、情绪识别、LLM、TTS 模型
- 录音并识别用户语音
- 预测音频情绪和文本情绪
- 生成中文回复
- 输出并播放合成语音

## 网页版运行

启动 Web 服务：

```bash
uvicorn voice_assistant_web:app --host 0.0.0.0 --port 8000
```

然后在浏览器里打开：

```text
http://127.0.0.1:8000
```

网页版支持：

- 浏览器内直接录音
- 上传到后端做 ASR 与情绪识别
- 展示文本、情绪结果和回复内容
- 自动播放生成的语音回复
- 提供 `/healthz` 和 `/readyz` 健康检查接口

## 正式上线部署

当前仓库已经整理成更适合上线的 FastAPI 结构：

- `voice_assistant_web.py` 作为后端入口
- `web_static/` 负责前端页面
- 浏览器录音后调用 `/api/analyze`
- 服务端会先用 `ffmpeg` 把录音转成标准 wav，再进入推理流程

### 环境变量

可以通过下面这些环境变量调整部署配置：

- `PORT`：服务端口，默认 `8000`
- `HOST`：监听地址，默认 `0.0.0.0`
- `EVA_TEMP_DIR`：临时文件目录，默认 `web_tmp/`
- `EVA_MODEL_PATH`：本地 GGUF 模型路径
- `EVA_WHISPER_MODEL`：Whisper 模型名，默认 `base`
- `EVA_TTS_MODEL`：TTS 模型名
- `EVA_LLM_THREADS`：LLM 线程数
- `EVA_LLM_CONTEXT`：LLM 上下文长度
- `EVA_LLM_GPU_LAYERS`：llama.cpp GPU layer 设置

### Docker 部署

构建镜像：

```bash
docker build -t emotion-voice-assistant .
```

运行容器：

```bash
docker run -p 8000:8000 \
  -e PORT=8000 \
  -e EVA_MODEL_PATH=/app/llama.cpp/models/qwen2.5-3b-instruct-q4_k_m.gguf \
  emotion-voice-assistant
```

然后访问：

```text
http://127.0.0.1:8000
```

### 上线前提

正式上线时，服务器至少需要准备：

- Python 运行环境
- `ffmpeg`
- Hugging Face / TTS 相关依赖
- 本地 GGUF 模型文件
- `emotion_audio/` 参考音频目录

如果这些文件没有跟着镜像或挂载目录一起提供，服务虽然会启动，但 `/readyz` 会显示未就绪。

## 让别人点击网页就能体验

如果你希望别人直接通过链接访问，这个项目不能只放在 GitHub Pages 这类静态托管上，因为它依赖后端 Python 服务、模型推理和语音生成。

你需要的是一个能运行 Python 服务的部署环境，例如云服务器或支持 Python Web 服务的平台。基本条件包括：

- 能运行 FastAPI / Uvicorn
- 能放下本地模型和语音资源文件
- 有足够的 CPU / 内存来跑 Whisper、情绪识别、TTS 和本地 LLM

当前项目的网页链路是：

1. 浏览器录音
2. 语音上传到后端
3. 后端执行 ASR、情绪识别、LLM、TTS
4. 返回文本结果和音频

这意味着真正上线时，服务器压力会明显高于普通展示型网页。

## 测试脚本

仓库里保留了一些独立测试脚本，方便分别调试各个模块：

- `python test_asr.py`
- `python test_audio_emotion.py`
- `python test_text_emotion.py`
- `python test_emotion_fusion.py`
- `python test_pipeline.py`
- `python test_tts.py`
- `python test_whisper_asr.py`

## 当前注意事项

- `emotion_audio/` 被 `.gitignore` 忽略，因此仓库里默认不包含情绪参考音频。
- `eva_assistant.py` 中引用了 `neutral.wav`，你本地需要准备对应文件。
- `voice_assistant_web.py` 是当前最适合演示给别人体验的入口。
- 浏览器录音文件会先经过 `ffmpeg` 转码，所以线上环境需要安装 `ffmpeg`。
- `emotion_pipeline.py` 当前使用的是 `emotion_recognition.*` 导入路径，而仓库实际目录是 `emotion/`，如果你要运行这个文件，可能需要先同步修正导入。
- 首次运行时会下载部分模型，耗时取决于网络和机器性能。
- 某些依赖对系统环境较敏感，尤其是 `torch`、`torchaudio`、`TTS` 和 `llama-cpp-python`。

## 适用场景

- 情绪陪伴助手原型
- 多模态情绪识别实验
- 中文语音交互 Demo
- 本地 LLM + TTS + Emotion 融合项目练习

## 后续可改进方向

- 增加 `requirements.txt` 或 `pyproject.toml`
- 增加更完整的安装说明
- 补充示例音频与效果展示
- 统一 ASR 路径和模块命名
- 提升情绪标签体系的一致性
- 增加异常处理与日志

## License

如果你准备公开长期维护，建议补充一个开源许可证文件，例如 MIT License。
