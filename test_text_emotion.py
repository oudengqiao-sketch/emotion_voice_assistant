from emotion_recognition.text_emotion import TextEmotionRecognizer

recognizer = TextEmotionRecognizer()

text = "I feel really sad today"

emotion = recognizer.predict_emotion(text)

print("Detected emotion:", emotion)