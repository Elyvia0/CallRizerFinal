
import threading
from collections.abc import Callable

import numpy as np
import soundcard as sc

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.5
CHUNK_FRAMES = int(SAMPLE_RATE * CHUNK_DURATION)


class AudioCapture:
    def __init__(
        self,
        on_audio: Callable[[str, np.ndarray], None],
        sample_rate: int = SAMPLE_RATE,
    ):
        self.on_audio = on_audio
        self.sample_rate = sample_rate
        self.stop_event = threading.Event()
        self.threads = []
        self.errors = []

    def list_devices(self) -> dict:
        microphone = sc.default_microphone()
        speaker = sc.default_speaker()

        loopbacks = sc.all_microphones(include_loopback=True)

        return {
            "microphone": microphone.name if microphone else None,
            "speaker": speaker.name if speaker else None,
            "loopbacks": [device.name for device in loopbacks],
        }

    def _capture(self, source, device):
        try:
            with device.recorder(
                samplerate=self.sample_rate,
                channels=2,
                blocksize=CHUNK_FRAMES,
            ) as recorder:
                while not self.stop_event.is_set():
                    audio = recorder.record(numframes=CHUNK_FRAMES)

                    if audio is None or len(audio) == 0:
                        continue

                    audio = np.asarray(audio, dtype=np.float32)

                    if audio.ndim == 2:
                        audio = audio.mean(axis=1)

                    self.on_audio(source, audio)

        except Exception as exc:
            if not self.stop_event.is_set():
                self.errors.append(f"{source}: {exc}")

    def start(self):
        if self.threads:
            raise RuntimeError("Audio capture has already been started.")

        self.stop_event.clear()
        self.errors.clear()

        microphone = sc.default_microphone()
        speaker = sc.default_speaker()

        if microphone is None:
            raise RuntimeError("No microphone was found.")

        if speaker is None:
            raise RuntimeError("No output speaker was found.")

        loopbacks = sc.all_microphones(include_loopback=True)

        system_device = next(
            (
                device
                for device in loopbacks
                if device.isloopback
                and device.name == speaker.name
            ),
            None,
        )

        if system_device is None:
            system_device = sc.get_microphone(
                id=str(speaker.name),
                include_loopback=True,
            )

        for source, device in [
            ("microphone", microphone),
            ("system", system_device),
        ]:
            thread = threading.Thread(
                target=self._capture,
                args=(source, device),
                name=f"callrizer-{source}",
                daemon=True,
            )
            self.threads.append(thread)
            thread.start()

    def stop(self):
        self.stop_event.set()

        for thread in self.threads:
            thread.join(timeout=3)

        self.threads.clear()
