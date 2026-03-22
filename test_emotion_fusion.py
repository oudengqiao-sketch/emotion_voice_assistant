from emotion_recognition.emotion_fusion import EmotionFusion

fusion = EmotionFusion()

audio_emotion = "sad"
text_emotion = "neutral"

final_emotion = fusion.fuse(audio_emotion, text_emotion)

print("Audio emotion:", audio_emotion)
print("Text emotion:", text_emotion)
print("Final emotion:", final_emotion)