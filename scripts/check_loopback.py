import time
import numpy as np
import soundcard as sc

devices = sc.all_microphones(include_loopback=True)

print("Available audio devices:")
for i, device in enumerate(devices):
    print(f"{i}: {device.name} | loopback={device.isloopback}")

loopbacks = [device for device in devices if device.isloopback]

if not loopbacks:
    print("ERROR: No loopback devices found.")
    raise SystemExit(1)

for device in loopbacks:
    print(f"\nTesting: {device.name}")
    input("Play audio on your computer, then press Enter...")

    try:
        with device.recorder(samplerate=48000, channels=2) as recorder:
            for i in range(5):
                audio = np.asarray(recorder.record(numframes=24000))
                peak = np.max(np.abs(audio)) if audio.size else 0
                rms = np.sqrt(np.mean(audio ** 2)) if audio.size else 0
                print(f"  Test {i + 1}: peak={peak:.6f}, rms={rms:.6f}")
                time.sleep(0.2)
    except Exception as exc:
        print(f"  ERROR: {type(exc).__name__}: {exc}")