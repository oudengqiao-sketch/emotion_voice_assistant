import json
import re
from pathlib import Path


class LongMemory:
    PATTERNS = {
        "likes": r"我喜欢([^。！？!?，,\n]+)",
        "dislikes": r"我讨厌([^。！？!?，,\n]+)",
        "fears": r"我害怕([^。！？!?，,\n]+)",
    }

    def __init__(self, memory_path: Path):
        self.memory_path = Path(memory_path)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self._memory = self._load()

    def _default_memory(self):
        return {
            "likes": [],
            "dislikes": [],
            "fears": [],
        }

    def _load(self):
        if not self.memory_path.exists():
            return self._default_memory()

        try:
            with open(self.memory_path, "r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
            memory = self._default_memory()
            if isinstance(data, dict):
                for key in memory:
                    value = data.get(key, [])
                    memory[key] = value if isinstance(value, list) else []
            return memory
        except (json.JSONDecodeError, OSError):
            return self._default_memory()

    def _save(self):
        with open(self.memory_path, "w", encoding="utf-8") as file_obj:
            json.dump(self._memory, file_obj, ensure_ascii=False, indent=2)

    def _normalize_value(self, text: str) -> str:
        return text.strip(" ：:，,。.!！?？\n\t")

    def update_from_text(self, text: str):
        updated = False

        for key, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                value = self._normalize_value(match)
                if value and value not in self._memory[key]:
                    self._memory[key].append(value)
                    updated = True

        if updated:
            self._save()

    def get_summary(self) -> str:
        parts = []
        for key in ("likes", "dislikes", "fears"):
            values = self._memory.get(key, [])
            if values:
                parts.append(f"{key}: {', '.join(values)}")

        return "\n".join(parts) if parts else "暂无长期记忆。"

    def get_memory(self):
        return dict(self._memory)
