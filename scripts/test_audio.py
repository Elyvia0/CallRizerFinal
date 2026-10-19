import threading
import time

from backend.audio.capture import AudioCapture


def main():
    received = {"microphone": 0, "system": 0}
    lock = threading.Lock()

    def on_audio(source, audio):
        with lock:
            received[source] += 1

        print(
            f"[{source.upper():10}] "
            f"samples={len(audio):5} "
            f"peak={abs(audio).max():.4f}"
        )

    capture = AudioCapture(on_audio=on_audio)

    print("Detected devices:")
    print(capture.list_devices())

    input("\nPress Enter to start capture...")

    try:
        capture.start()
        print("\nCapturing audio for 15 seconds.")
        print("Speak into your microphone and play audio on your computer.")

        time.sleep(15)

    except KeyboardInterrupt:
        print("\nCapture interrupted.")

    finally:
        capture.stop()

    print("\nCapture results:")
    print(f"Microphone chunks: {received['microphone']}")
    print(f"System chunks:     {received['system']}")

    if capture.errors:
        print("\nErrors:")
        for error in capture.errors:
            print(error)

    if all(count > 0 for count in received.values()):
        print("\nSUCCESS: Both audio sources produced audio chunks.")
    else:
        print("\nCHECK: One or both audio sources produced no chunks.")


if __name__ == "__main__":
    main()