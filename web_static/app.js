let mediaRecorder;
let chunks = [];

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const clearBtn = document.getElementById("clearBtn");
const logBox = document.getElementById("log");
const statusPill = document.getElementById("status");
const player = document.getElementById("player");
const timing = document.getElementById("timing");

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function log(message) {
  logBox.textContent = message;
}

function setStatus(text) {
  statusPill.textContent = text;
}

function resetUI() {
  setText("userText", "-");
  setText("audioEmotion", "-");
  setText("textEmotion", "-");
  setText("finalEmotion", "-");
  setText("replyText", "-");
  setText("replyEmotion", "-");
  setText("replyBox", "等待生成...");
  timing.textContent = "等待分析结果...";
  player.pause();
  player.src = "";
  log("等待录音...");
  setStatus("待机中");
}

async function sendAudio(blob) {
  const formData = new FormData();
  formData.append("file", blob, "recording.webm");

  log("正在上传录音并分析，请稍候...");
  setStatus("分析中");
  timing.textContent = "模型推理中...";

  const response = await fetch("/api/analyze", {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) {
    const detail = data.detail || "未知错误";
    throw new Error(detail);
  }

  setText("userText", data.user_text);
  setText("audioEmotion", data.audio_emotion);
  setText("textEmotion", data.text_emotion);
  setText("finalEmotion", data.final_emotion);
  setText("replyText", data.reply);
  setText("replyEmotion", data.reply_emotion);
  setText("replyBox", data.reply);
  timing.textContent = `分析完成，用时 ${data.elapsed_sec} 秒`;
  player.src = `data:audio/wav;base64,${data.audio_base64}`;
  await player.play().catch(() => {});
  log("分析完成，结果已返回。");
  setStatus("完成");
}

startBtn.onclick = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];

    mediaRecorder.ondataavailable = (event) => chunks.push(event.data);
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks, { type: "audio/webm" });
      try {
        await sendAudio(blob);
      } catch (error) {
        log(`分析失败：${error.message}`);
        setStatus("失败");
        timing.textContent = "请检查服务端日志";
      } finally {
        stream.getTracks().forEach((track) => track.stop());
      }
    };

    mediaRecorder.start();
    startBtn.disabled = true;
    stopBtn.disabled = false;
    log("录音中，请对着麦克风说话...");
    setStatus("录音中");
    timing.textContent = "正在采集浏览器音频";
  } catch (error) {
    log(`无法开始录音：${error.message}`);
    setStatus("失败");
    timing.textContent = "请检查浏览器麦克风权限";
  }
};

stopBtn.onclick = () => {
  if (!mediaRecorder || mediaRecorder.state === "inactive") {
    return;
  }

  mediaRecorder.stop();
  startBtn.disabled = false;
  stopBtn.disabled = true;
  setStatus("上传中");
  timing.textContent = "录音结束，准备上传";
};

clearBtn.onclick = resetUI;

resetUI();
