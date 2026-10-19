# Phase 2: Audio Capture Pipeline

## 🎯 Objectives

Implement robust, low-latency audio capture for both microphone input (user speech) and system audio loopback (incoming call audio on Windows), piping captured PCM audio buffers into the Python backend processing engine.

---

## 🎧 Audio Architecture

```
[ Microphone Input ]  -------->  [ Audio Stream Manager ]
                                         |
[ System Loopback (WASAPI) ] --->  (Ring Buffer / Resampling: 16kHz Mono)
                                         |
                                         v
                              [ Audio Chunk Dispatcher ]
                                         |
                                         v
                            (Internal Queue / Streaming WS)
```

---

## 📋 Implementation Checklist

### 1. Audio Capture Service (`backend/audio/`)
- [ ] Device Discovery: Enumerate available input devices and Windows WASAPI loopback output devices.
- [ ] Dual-Channel Capture:
  - Capture local microphone audio.
  - Capture remote call audio via Windows WASAPI loopback.
- [ ] Audio Formatting:
  - Resample captured audio to 16,000 Hz, 16-bit PCM, single-channel (mono).
  - Normalize and prevent audio clipping.
- [ ] Ring Buffer / Queue:
  - Implement a thread-safe ring buffer to handle audio bursts without dropping samples.
  - Maintain low audio latency (< 100ms processing delay).

### 2. Audio Control API
- [ ] `POST /api/audio/start`: Start audio capture on selected devices.
- [ ] `POST /api/audio/stop`: Stop audio capture cleanly.
- [ ] `GET /api/audio/devices`: List available input and loopback audio devices.
- [ ] `GET /api/audio/status`: Retrieve capture health (dropped frames, current volume/RMS).

### 3. Desktop UI Integration
- [ ] Add Audio Device Selector in the desktop Settings page (`desktop/src/pages/Settings.tsx`).
- [ ] Implement live VU/Volume meter in the desktop top bar (`desktop/src/components/AudioMeter.tsx`).
- [ ] Add start/stop call recording toggle in the main dashboard.

---

## ✅ Acceptance Criteria

1. Device enumeration reliably detects both microphone and system loopback devices on Windows.
2. Starting capture streams continuous 16kHz mono audio chunks without buffer underruns.
3. Audio capture handles device unplug/disconnect events gracefully without crashing the backend.
4. Unit tests in `backend/tests/unit/test_audio.py` validate buffer slicing and resampling logic.
