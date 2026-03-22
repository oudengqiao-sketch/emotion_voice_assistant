from emotion_pipeline import EmotionPipeline

pipeline = EmotionPipeline()

result = pipeline.process("test.wav")

print("\n=== RESULT ===")
print(result)