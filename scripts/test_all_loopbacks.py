import time
import numpy as np
import soundcard as sc

devices = sc.all_microphones(include_loopback=True)

for device in devices:
    print(f"\nTesting: {device.name} | loopback={device.isloopback}")

    try:
        with device.recorder(samplerate=48000) as recorder:
            input("Play audio through your realme buds, then press Enter...")
            for i in range(3):
                audio = np.asarray(recorder.record(numframes=24000))
                print(
                    f"peak={np.max(np.abs(audio)):.6f}, "
                    f"rms={np.sqrt(np.mean(audio ** 2)):.6f}"
                )
                time.sleep(0.2)
    except Exception as e:
        print(f"ERROR: {e}")