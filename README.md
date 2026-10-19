# Callrizer

**Never get caught zoning out on a call.**

Callrizer is an AI assistant that listens to a live voice call on your device. When someone on the call is talking *to you* (asking you a question or waiting for your reply) while you're multitasking, Callrizer alerts you instantly and shows a short summary of what was asked and what the conversation was about. You can respond confidently instead of saying "sorry, can you repeat that?"

> Status: early development (MVP phase). Team of 3.

---

## The problem

People multitask during calls. When they get addressed, they've missed the question and the context, and the other person feels ignored.

## What Callrizer does

1. Captures the call audio on your device (with your consent and a visible "listening" indicator).
2. Transcribes it in real time with speaker labels.
3. Detects when the conversation is directed at you (name mention, question plus pause, or LLM intent check).
4. Fires an alert (sound plus on-screen overlay, optional phone push).
5. Shows a two-line summary: **Asked:** the question. **Context:** what was being discussed.

Target latency: under ~3 seconds from the end of the question to the alert.

## Platform scope (important)

| Platform | Support | Notes |
|---|---|---|
| Desktop (Windows / macOS) calls: WhatsApp Desktop, Google Meet, Zoom, Teams, Discord | **MVP target** | Captured via system audio loopback plus mic |
| Mobile WhatsApp / Instagram calls | **Not in MVP** | These calls are end-to-end encrypted and mobile OSes generally block third-party call-audio capture (to be verified per OS version). Mobile will be a companion app for receiving alerts. |

## Architecture

```
[System audio + Mic]
        |
        v
[Desktop app: capture + overlay]  <--WebSocket-->  [Backend (FastAPI)]
                                                      |
                                    +-----------------+-----------------+
                                    |                 |                 |
                              Streaming STT     Trigger engine     Summarizer (LLM)
                              (speaker labels)  (name / question   (Asked + Context)
                                                 / LLM classifier)
                                                      |
                                                      v
                                       Alert -> overlay + sound + phone push
```

## Tech stack

- **Desktop app:** Tauri (or Electron) plus React overlay UI
- **Backend:** Python 3.11+, FastAPI, WebSockets
- **Speech-to-text:** Deepgram or AssemblyAI streaming (Whisper-based as fallback)
- **LLM:** fast, cheap model (Claude Haiku-class or Gemini Flash-class)
- **Push notifications:** Firebase Cloud Messaging or OneSignal

## Repo structure (planned)

```
callrizer/
├── README.md
├── IMPLEMENTATION.md
├── desktop/          # Tauri/Electron app: audio capture, overlay, settings
├── backend/          # FastAPI: STT streaming, triggers, summarizer
├── prototypes/       # Isolated audio-capture and latency experiments
├── eval/             # Test dataset + scripts to measure false alarms / misses
└── docs/
```

## Getting started

```bash
git clone <your-repo-url>
cd callrizer

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # add your API keys
uvicorn app.main:app --reload
```

Desktop app setup instructions will be added once the Week 1 audio-capture prototype is validated.

## Environment variables

```
STT_API_KEY=
LLM_API_KEY=
PUSH_API_KEY=
USER_NAME_VARIANTS=Raghav,Raghavendra   # names/nicknames to listen for
```

## Privacy and consent

- Callrizer processes audio **only while the user has it switched on**, with a visible indicator.
- Audio is streamed for transcription and not stored by default; transcripts live in memory (rolling 60-90 s window).
- Recording or transcribing other people's speech is regulated differently by country. Users are responsible for informing participants where required. A full privacy policy is required before any public release.

## Roadmap

- [ ] Week 1: prove system-audio capture on a real call
- [ ] Weeks 2-3: end-to-end pipeline with name-mention trigger and summary alert
- [ ] Week 4: question/intent classifier, reduce false alarms
- [ ] Weeks 5-6: polish, closed beta, measure precision/recall
- [ ] Later: mobile companion app, wearable alerts, more languages

## Team

Team of 3: Audio and Desktop, AI Pipeline, Product/UI/Testing. See `IMPLEMENTATION.md` for ownership.

## License

TBD