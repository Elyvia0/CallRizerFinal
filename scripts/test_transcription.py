
import time
import threading
import numpy as np

from backend.audio.capture import AudioCapture
from backend.transcription.whisper_service import WhisperTranscriptionService


def main():
    print("[1/5] Loading Whisper model...", flush=True)

    try:
        service = WhisperTranscriptionService(model_size="base")
    except Exception as exc:
        print(f"MODEL ERROR: {exc}", flush=True)
        return

    print("[2/5] Whisper model loaded.", flush=True)

    chunks = {"microphone": [], "system": []}
    lock = threading.Lock()

    def on_audio(source, audio):
        with lock:
            chunks[source].append(audio.copy())

    capture = AudioCapture(on_audio=on_audio)

    try:
        print("[3/5] Starting audio capture...", flush=True)
        capture.start()
        print("[4/5] Recording for 10 seconds. Speak now!", flush=True)
        time.sleep(10)

    except KeyboardInterrupt:
        print("Recording interrupted.", flush=True)

    except Exception as exc:
        print(f"CAPTURE ERROR: {exc}", flush=True)

    finally:
        capture.stop()

    for source in ("microphone", "system"):
        with lock:
            audio_chunks = chunks[source].copy()

        print(
            f"\n{source.upper()}: received {len(audio_chunks)} chunks",
            flush=True,
        )

        if not audio_chunks:
            continue

        audio = np.concatenate(audio_chunks)
        print(f"Audio samples: {len(audio)}", flush=True)
        print("[5/5] Transcribing...", flush=True)

        try:
            start = time.time()
            text = service.transcribe(audio, sample_rate=16000)
            print(f"Transcript: {text or '[No speech detected]'}", flush=True)
            print(f"Time: {time.time() - start:.2f}s", flush=True)
        except Exception as exc:
            print(f"TRANSCRIPTION ERROR: {exc}", flush=True)

    if capture.errors:
        print("\nCapture errors:", flush=True)
        for error in capture.errors:
            print(error, flush=True)

    print("\nTest finished.", flush=True)


if __name__ == "__main__":
    main()
