from pathlib import Path

from memory.emotion_memory import EmotionMemory
from memory.long_memory import LongMemory
from memory.short_memory import ShortMemory


class MemoryManager:
    def __init__(self, root_dir: Path, short_limit: int = 8, emotion_limit: int = 10):
        base_dir = Path(root_dir) / "memory" / "data"
        self.short_memory = ShortMemory(base_dir / "short_memory.json", max_turns=short_limit)
        self.long_memory = LongMemory(base_dir / "long_memory.json")
        self.emotion_memory = EmotionMemory(base_dir / "emotion_memory.json", max_items=emotion_limit)

    def get_context(self):
        return {
            "recent_history": self.short_memory.build_context(),
            "long_term_memory": self.long_memory.get_summary(),
            "emotion_trend": self.emotion_memory.get_trend(),
        }

    def save_turn(self, user_text: str, assistant_reply: str, emotion: str):
        self.short_memory.add_turn(
            user_text=user_text,
            assistant_reply=assistant_reply,
            emotion=emotion,
        )
        self.long_memory.update_from_text(user_text)
        self.emotion_memory.add_emotion(emotion)
