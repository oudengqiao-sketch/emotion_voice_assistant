import torch
import torchaudio
from transformers import Wav2Vec2FeatureExtractor, AutoModelForAudioClassification


class AudioEmotionRecognizer:

    def __init__(self):

        model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"

        print("Loading audio emotion model...")

        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
        self.model = AutoModelForAudioClassification.from_pretrained(model_name)

        self.labels = self.model.config.id2label

        print("Audio emotion model loaded")

    def predict_emotion(self, audio_path):

        speech, sr = torchaudio.load(audio_path)

        # resample
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            speech = resampler(speech)

        speech = speech.squeeze()

        # feature extract
        inputs = self.feature_extractor(
            speech,
            sampling_rate=16000,
            return_tensors="pt"
        )

        # inference
        with torch.no_grad():
            logits = self.model(**inputs).logits

        predicted_id = torch.argmax(logits, dim=-1).item()

        emotion = self.labels[predicted_id]

        # 统一标签
        mapping = {
            "hap": "happy",
            "happy": "happy",

            "sad": "sad",
            "sadness": "sad",

            "ang": "angry",
            "anger": "angry",

            "neu": "neutral",
            "neutral": "neutral",

            "fear": "fear",
            "fearful": "fear"
        }

        emotion = mapping.get(emotion.lower(), "neutral")

        return emotion