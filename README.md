# Emotion Voice Assistant

一个中文情绪语音助手项目，整合了语音录制、语音识别、音频情绪识别、文本情绪识别、情绪融合、大语言模型回复，以及情绪化语音合成。

项目目标是让助手不仅能“听懂你说了什么”，还能尽量判断你说话时的情绪，并用更贴近情绪状态的语气回复。

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
├── emotion_pipeline.py
├── record_audio.py
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

安装你项目中会用到的核心依赖：

```bash
pip install numpy sounddevice wave
pip install torch torchaudio transformers
pip install openai-whisper faster-whisper
pip install TTS
pip install llama-cpp-python
```

如果你在 macOS 上运行语音播放，代码里当前使用的是 `afplay`。

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
