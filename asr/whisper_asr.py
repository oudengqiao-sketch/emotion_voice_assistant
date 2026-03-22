import whisper


class WhisperASR:

    def __init__(self):

        print("Loading Whisper model...")

        self.model = whisper.load_model("base")

        print("Whisper model loaded")

    def transcribe(self, audio_path):

        result = self.model.transcribe(audio_path)

        return result["text"]