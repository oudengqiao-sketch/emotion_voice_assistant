from asr.whisper_asr import WhisperASR
from emotion_recognition.audio_emotion import AudioEmotionRecognizer
from emotion_recognition.text_emotion import TextEmotionRecognizer
from emotion_recognition.emotion_fusion import EmotionFusion


class EmotionPipeline:

    def __init__(self):

        print("Initializing Emotion Pipeline...")

        self.asr = WhisperASR()
        self.audio_emotion = AudioEmotionRecognizer()
        self.text_emotion = TextEmotionRecognizer()
        self.fusion = EmotionFusion()

        print("Pipeline ready")

    def process(self, audio_path):

        print("\n--- Step 1: Speech Recognition ---")
        text = self.asr.transcribe(audio_path)
        print("Text:", text)

        print("\n--- Step 2: Audio Emotion ---")
        audio_emotion = self.audio_emotion.predict_emotion(audio_path)
        print("Audio Emotion:", audio_emotion)

        print("\n--- Step 3: Text Emotion ---")
        text_emotion = self.text_emotion.predict_emotion(text)
        print("Text Emotion:", text_emotion)

        print("\n--- Step 4: Emotion Fusion ---")
        final_emotion = self.fusion.fuse(audio_emotion, text_emotion)
        print("Final Emotion:", final_emotion)

        return {
            "text": text,
            "audio_emotion": audio_emotion,
            "text_emotion": text_emotion,
            "final_emotion": final_emotion
        }