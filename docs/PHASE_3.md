# Phase 3: Speech-to-Text & Real-Time Transcription

## 🎯 Objectives

Integrate a high-performance, local Speech-to-Text (STT) pipeline using Voice Activity Detection (VAD) and Whisper (via `faster-whisper`), streaming transcribed speech segments in real-time to the desktop UI.

---

## 🎙️ Transcription Pipeline Architecture

```
[ Captured Audio Stream ]
            |
            v
[ Voice Activity Detection (Silero VAD) ]
            |
            +---> Speech Detected? 
                     |
                     | Yes
                     v
       [ Audio Chunk Accumulator ]
                     |
                     v
   [ faster-whisper Model Worker (CTranslate2) ]
                     |
                     v
      [ Segment / Word Timestamps ]
                     |
                     v
    [ WebSocket Dispatcher (/ws/transcripts) ]
                     |
                     v
       [ Desktop App Live Display ]
```

---

## 📋 Implementation Checklist

### 1. VAD & Preprocessing (`backend/transcription/vad.py`)
- [ ] Integrate lightweight voice activity detection to filter out background noise and silence.
- [ ] Implement audio windowing (e.g., 2–5 second chunks or speech-boundary chunking).

### 2. Transcription Engine (`backend/transcription/engine.py`)
- [ ] Initialize `faster-whisper` model (`base` or `small` with `int8` quantization for efficient CPU/GPU inference).
- [ ] Implement asynchronous worker thread to avoid blocking the FastAPI event loop during transcription.
- [ ] Generate real-time partial hypotheses (interim transcripts) and finalized segments.
- [ ] Add speaker differentiation flag (Local Mic vs. Remote System Audio).

### 3. API & WebSocket Streaming
- [ ] Stream transcribed messages via WebSocket:
  ```json
  {
    "type": "transcript_segment",
    "speaker": "remote" | "local",
    "text": "Hello, thank you for calling support.",
    "is_final": true,
    "timestamp": 1713500000.123
  }
  ```
- [ ] REST endpoints to configure model size, language, and transcription sensitivity.

### 4. Desktop UI Transcript View (`desktop/src/pages/LiveCall.tsx`)
- [ ] Auto-scrolling live transcript message feed.
- [ ] Distinct visual styling for local speaker vs. remote speaker.
- [ ] Real-time typing/partial segment indicator.
- [ ] Export transcript button (JSON / TXT).

---

## ✅ Acceptance Criteria

1. Speech is transcribed locally with under 1.5 seconds end-to-end latency on standard hardware.
2. Silence and non-speech background sounds are filtered by VAD without triggering hallucinations.
3. Transcribed segments accurately label whether the speaker is local (microphone) or remote (system audio).
4. Desktop UI displays transcripts in real time with auto-scroll and speaker badges.
