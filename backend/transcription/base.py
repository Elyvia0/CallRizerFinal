from abc import ABC, abstractmethod
import numpy as np


class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        pass