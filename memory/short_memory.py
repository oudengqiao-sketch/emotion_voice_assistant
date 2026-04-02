import json
from datetime import datetime
from pathlib import Path


class ShortMemory:
    def __init__(self, memory_path: Path, max_turns: int = 8):
        self.memory_path = Path(memory_path)
        self.max_turns = max_turns
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self._memory = self._load()

    def _load(self):
        if not self.memory_path.exists():
            return []

        try:
            with open(self.memory_path, "r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self):
        with open(self.memory_path, "w", encoding="utf-8") as file_obj:
            json.dump(self._memory, file_obj, ensure_ascii=False, indent=2)

    def add_turn(self, user_text: str, assistant_reply: str, emotion: str, timestamp: str | None = None):
        self._memory.append(
            {
                "user_text": user_text,
                "assistant_reply": assistant_reply,
                "emotion": emotion,
                "timestamp": timestamp or datetime.now().isoformat(timespec="seconds"),
            }
        )
        self._memory = self._memory[-self.max_turns:]
        self._save()

    def get_recent_turns(self, limit: int | None = None):
        if limit is None:
            return list(self._memory)
        return self._memory[-limit:]

    def build_context(self, limit: int | None = None) -> str:
        turns = self.get_recent_turns(limit=limit)
        if not turns:
            return "暂无最近对话。"

        lines = []
        for item in turns:
            lines.append(
                f"[{item['timestamp']}] 用户({item['emotion']}): {item['user_text']}\n"
                f"助手: {item['assistant_reply']}"
            )
        return "\n".join(lines)
