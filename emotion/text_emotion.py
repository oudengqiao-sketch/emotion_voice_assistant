from transformers import pipeline


class TextEmotionRecognizer:

    def __init__(self):

        print("Loading Chinese sentiment model...")

        self.classifier = pipeline(
            "sentiment-analysis",
            model="IDEA-CCNL/Erlangshen-RoBERTa-110M-Sentiment"
        )

        print("Text emotion model loaded")

    def predict_emotion(self, text):

        # -------- 关键词优先 --------

        sad_words = ["伤心", "难过", "失望", "崩溃", "不好"]
        angry_words = ["生气", "气死", "烦", "讨厌"]
        happy_words = ["开心", "高兴", "快乐", "太棒"]

        for w in sad_words:
            if w in text:
                return "sad"

        for w in angry_words:
            if w in text:
                return "angry"

        for w in happy_words:
            if w in text:
                return "happy"

        # -------- 模型判断 --------

        result = self.classifier(text)[0]

        label = result["label"]

        if label == "Positive":
            return "happy"

        if label == "Negative":
            return "sad"

        return "neutral"