# Emotion Voice Agent

一个中文情绪陪伴多模态 Agent 系统。

这个项目最初是一个“情绪语音助手”，现在已经逐步演进为一个具备以下能力的本地 Agent：

- 语音输入与 ASR 识别
- 音频 + 文本双通道情绪识别
- 短期记忆、长期记忆、情绪记忆
- 规则驱动 Tool 调用
- 轻量 RAG（persona + 长期记忆增强）
- Agent Brain 统一决策
- 本地 LLM 回复生成
- XTTS 情绪语音合成

项目目标不是做一个“冷冰冰的问答机器人”，而是做一个更像陪伴型数字人的多模态交互系统。

## 当前能力概览

当前仓库已经包含以下系统层级：

- `Emotion`：理解用户当前情绪
- `Memory`：记住最近对话、长期偏好与情绪趋势
- `Tool`：具备基础执行能力
- `RAG`：强化 persona 设定与长期记忆参考
- `Agent Brain`：统一调度 Tool / Memory / RAG / Prompt / LLM
- `TTS`：把最终回复转换成语音

## 用户从输入到输出的完整流程

1. 用户说话，系统开始录音
2. `ASR` 将语音转换成文本
3. `Emotion` 模块分别识别：
   - 音频情绪
   - 文本情绪
4. `Emotion Fusion` 生成最终情绪
5. `Agent Brain` 开始统一决策：
   - 读取 memory context
   - 判断是否调用 tool
   - 执行 tool
   - 调用 RAG retrieve
   - 使用 Prompt Builder 拼出统一 prompt
   - 调用 LLM
6. 系统解析 LLM 输出：
   - 回复情绪
   - 回复文本
7. Memory 写回当前轮对话
8. TTS 根据回复内容与情绪合成语音
9. 最终播放给用户

一句话概括当前系统链路：

```text
语音输入 -> ASR -> Emotion -> Memory/Tool/RAG -> Agent Brain -> LLM -> TTS -> 语音输出
```

## 架构分层

### 1. Emotion Layer

负责识别用户当前情绪。

- `emotion/audio_emotion.py`
- `emotion/text_emotion.py`
- `emotion/emotion_fusion.py`

作用：

- 从语音信号判断情绪
- 从文本内容判断情绪
- 将二者融合为最终情绪标签

当前统一情绪标签包括：

- `happy`
- `sad`
- `angry`
- `neutral`
- `fear`
- `confused`

### 2. Memory Layer

负责让系统具备“持续记住用户”的能力。

目录：

- `memory/short_memory.py`
- `memory/long_memory.py`
- `memory/emotion_memory.py`
- `memory/memory_manager.py`

功能：

- `short-term memory`
  - 保存最近 5~10 轮对话
  - 每轮记录 `user_text`、`assistant_reply`、`emotion`、`timestamp`
- `long-term memory`
  - 用规则法抽取用户长期偏好与事实
  - 例如：
    - `我喜欢...` -> `likes`
    - `我讨厌...` -> `dislikes`
    - `我害怕...` -> `fears`
- `emotion memory`
  - 记录最近多次情绪
  - 输出 `positive / neutral / negative` 趋势

### 3. Tool Layer

负责让系统从“只能聊天”升级为“能做事”。

目录：

- `tools/registry.py`
- `tools/get_time.py`
- `tools/get_weather.py`
- `tools/save_journal.py`
- `tools/emotion_checkin.py`

当前工具：

- `get_time`
- `get_weather`
- `save_journal`
- `emotion_checkin`

特点：

- 规则驱动，不做复杂 function calling
- 所有 tool 都通过 `ToolRegistry` 统一注册与调用
- 当前输出已统一为结构化 dict / JSON 形式

### 4. RAG Layer

负责给系统增加设定一致性和记忆增强。

目录：

- `rag/knowledge_base.py`
- `rag/retriever.py`

当前实现是轻量版本：

- 没有引入向量数据库
- 没有用 FAISS / Chroma
- 主要作用是把 persona 设定与长期记忆一起注入 prompt

当前 persona 重点：

- 温柔
- 耐心
- 共情
- 不说教
- 不像客服
- 回复适合 TTS 播放

### 5. Agent Brain Layer

这是当前系统的核心升级点。

目录：

- `agent/prompt_builder.py`
- `agent/agent_brain.py`

职责：

- 统一读取 memory context
- 统一决定 tool 调用
- 统一触发 RAG
- 统一构造 prompt
- 统一调用 LLM

`Agent Brain` 让项目从“模块拼接”变成了“统一决策系统”。

### 6. Generation & Voice Layer

负责生成回复与语音输出。

- `llama.cpp / llama_cpp`
- `TTS.api / XTTS`

流程：

- Agent Brain 生成 prompt
- LLM 输出带情绪标签的回复
- `parse_llm()` 解析出回复情绪与正文
- `speak()` 用 XTTS 合成音频

## 当前项目结构

```text
emotion_voice_assistant/
├── agent/
│   ├── agent_brain.py
│   └── prompt_builder.py
├── asr/
│   └── whisper_asr.py
├── emotion/
│   ├── audio_emotion.py
│   ├── emotion_fusion.py
│   └── text_emotion.py
├── memory/
│   ├── emotion_memory.py
│   ├── long_memory.py
│   ├── memory_manager.py
│   └── short_memory.py
├── rag/
│   ├── knowledge_base.py
│   └── retriever.py
├── tools/
│   ├── emotion_checkin.py
│   ├── get_time.py
│   ├── get_weather.py
│   ├── registry.py
│   └── save_journal.py
├── tts/
│   └── test_tts.py
├── web_static/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── Dockerfile
├── eva_assistant.py
├── emotion_pipeline.py
├── record_audio.py
├── requirements.txt
├── voice_assistant_web.py
└── README.md
```

## 核心入口

### 命令行入口

- `eva_assistant.py`

当前主流程已经被压缩成：

```text
ASR -> Emotion -> run_agent -> TTS
```

其中：

- Tool 决策
- RAG 调用
- Prompt 拼接

都已经被移到 Agent Brain 中统一处理。

### Web Demo

- `voice_assistant_web.py`
- `web_static/`

这个版本适合网页演示，但当前主 README 的重点已经从“普通 Web Demo”升级为“多模态陪伴 Agent 系统”。

## 关键模块协作关系

### Prompt Builder

`agent/prompt_builder.py` 统一拼接：

1. persona
2. short-term memory
3. long-term memory
4. emotion + emotion trend
5. RAG context
6. tool result
7. user input

它的目标是让系统始终保持陪伴型数字人的风格一致性。

### Agent Brain

`agent/agent_brain.py` 的 `run_agent()` 当前负责：

1. 获取 memory context
2. `decide_tool()`
3. `call_tool()`
4. `retrieve()`
5. `build_prompt()`
6. `llm()`

这就是当前项目的统一决策层。

## 技术栈

- Python
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [Transformers](https://github.com/huggingface/transformers)
- [PyTorch](https://pytorch.org/)
- [Coqui TTS](https://github.com/coqui-ai/TTS)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- FastAPI（Web Demo）

## 运行前准备

建议使用 Python 3.10 或 3.11，并先创建虚拟环境。

```bash
python -m venv venv
source venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 模型与资源

当前项目依赖以下本地资源：

- 本地 GGUF 大模型文件  
  `llama.cpp/models/qwen2.5-3b-instruct-q4_k_m.gguf`
- 情绪参考音频目录  
  `emotion_audio/`
- XTTS 模型
- Whisper / Faster-Whisper 模型
- Hugging Face 情绪识别模型

注意：

- 模型文件和参考音频通常较大
- 仓库默认不包含这些资源
- 需要你在本地自行准备

## 运行方式

启动命令行版：

```bash
python eva_assistant.py
```

当前一轮交互会完成：

- 录音
- ASR 转写
- 情绪识别与融合
- Agent Brain 决策
- Tool / RAG / Memory 注入
- LLM 回复生成
- Memory 写回
- TTS 播放

## 网页版运行

启动 Web Demo：

```bash
uvicorn voice_assistant_web:app --host 0.0.0.0 --port 8000
```

浏览器访问：

```text
http://127.0.0.1:8000
```

## 当前系统特点

和最初版本相比，现在这个项目的核心变化是：

- 不再只是“语音输入 + LLM + TTS”
- 开始具备“情绪理解 + 记忆 + 工具 + 检索增强 + 决策脑”的 Agent 特征

也就是说，它已经从一个简单语音助手，升级成了一个：

**情绪陪伴多模态 Agent 系统**

## 后续可继续扩展方向

- 更强的长期记忆抽取策略
- 更丰富的 Tool 集合
- 更强的 RAG 检索策略
- 真正的 Planning / Task Decomposition
- Streaming 语音输出
- 前后端统一的 Agent UI
- 多用户会话隔离

## 注意事项

- `emotion_audio/` 被 `.gitignore` 忽略，因此仓库中默认不包含音色参考文件
- `memory/data/` 也是运行时目录，默认不提交
- `voice_assistant_web.py` 仍然是可运行的 Web Demo，但当前主架构重点是 Agent 化升级
- 首次运行模型下载可能较慢
- 某些依赖对系统环境较敏感，尤其是 `torch`、`torchaudio`、`TTS` 和 `llama-cpp-python`

## License

如果你准备长期公开维护，建议补充一个开源许可证文件，例如 MIT License。
