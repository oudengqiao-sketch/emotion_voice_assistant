import json
from datetime import datetime
from pathlib import Path


class EmotionMemory:
    POSITIVE_EMOTIONS = {"happy"}
    NEGATIVE_EMOTIONS = {"sad", "angry", "fear", "confused"}

    def __init__(self, memory_path: Path, max_items: int = 10):
        self.memory_path = Path(memory_path)
        self.max_items = max_items
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

    def add_emotion(self, emotion: str, timestamp: str | None = None):
        self._memory.append(
            {
                "emotion": emotion,
                "timestamp": timestamp or datetime.now().isoformat(timespec="seconds"),
            }
        )
        self._memory = self._memory[-self.max_items:]
        self._save()

    def get_recent_emotions(self):
        return list(self._memory)

    def get_trend(self) -> str:
        if not self._memory:
            return "neutral"

        score = 0
        for item in self._memory:
            emotion = item.get("emotion", "neutral")
            if emotion in self.POSITIVE_EMOTIONS:
                score += 1
            elif emotion in self.NEGATIVE_EMOTIONS:
                score -= 1

        average = score / len(self._memory)
        if average > 0.2:
            return "positive"
        if average < -0.2:
            return "negative"
        return "neutral"
