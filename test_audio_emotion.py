from emotion_recognition.audio_emotion import AudioEmotionRecognizer

recognizer = AudioEmotionRecognizer()

emotion = recognizer.predict_emotion("sad.wav")

print("Detected emotion:", emotion)