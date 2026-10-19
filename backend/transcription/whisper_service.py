import numpy as np
from faster_whisper import WhisperModel
from backend.transcription.base import TranscriptionService


class WhisperTranscriptionService(TranscriptionService):
    def __init__(self, model_size: str = "base"):
        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
        )

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
    ) -> str:
        audio = np.asarray(audio, dtype=np.float32).flatten()

        if sample_rate != 16000:
            raise ValueError("Audio must be sampled at 16000 Hz.")

        if audio.size == 0 or np.max(np.abs(audio)) < 0.005:
            return ""

        segments, _ = self.model.transcribe(
            audio,
            beam_size=1,
            vad_filter=True,
        )

        return " ".join(segment.text.strip() for segment in segments).strip()