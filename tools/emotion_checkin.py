def emotion_checkin(emotion: str, memory_manager):
    memory_manager.emotion_memory.add_emotion(emotion)
    trend = memory_manager.emotion_memory.get_trend()
    return {
        "tool": "emotion_checkin",
        "emotion": emotion,
        "trend": trend,
    }
