import time
import threading
import numpy as np

from backend.audio.capture import AudioCapture
from backend.transcription.whisper_service import (
    WhisperTranscriptionService,
)


def main():
    service = WhisperTranscriptionService(model_size="base")

    chunks = {"microphone": [], "system": []}
    lock = threading.Lock()

    def on_audio(source, audio):
        with lock:
            chunks[source].append(audio.copy())

    capture = AudioCapture(on_audio=on_audio)

    print("Starting audio capture...")
    print("Speak a complete sentence into your microphone.")
    print("Capture will run for 10 seconds.")

    try:
        capture.start()
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        capture.stop()

    for source in ("microphone", "system"):
        with lock:
            audio_chunks = chunks[source].copy()

        if not audio_chunks:
            print(f"\n{source.upper()}: No audio received.")
            continue

        audio = np.concatenate(audio_chunks)

        print(f"\nTranscribing {source.upper()}...")
        start = time.time()

        try:
            text = service.transcribe(audio, sample_rate=16000)
            print(f"Transcript: {text or '[No speech detected]'}")
            print(f"Processing time: {time.time() - start:.2f}s")
        except Exception as exc:
            print(f"Transcription error: {exc}")

    if capture.errors:
        print("\nCapture errors:")
        for error in capture.errors:
            print(error)


if __name__ == "__main__":
    main()