class EmotionFusion:

    def __init__(self):
        print("Emotion fusion module ready")

    def fuse(self, audio_emotion, text_emotion):

        # 如果一致
        if audio_emotion == text_emotion:
            return audio_emotion

        # 如果语音不是neutral，优先语音
        if audio_emotion != "neutral":
            return audio_emotion

        # 否则使用文本情绪
        return text_emotion