# Callrizer — Implementation Plan

**Status:** MVP specification  
**Initial platform:** Windows desktop  
**Team size:** 3

This document defines the implementation architecture, component responsibilities, message contracts, trigger logic, evaluation process, and development milestones.

All team members should follow the same interfaces. Changes to shared contracts must be agreed upon and documented before implementation.

---

## 1. Goal and Success Metrics

Callrizer detects when someone on a live call may be directing a question or request at the user, then presents a concise alert containing the question and relevant conversational context.

### Initial Targets

| Metric | Target |
|---|---:|
| Alert precision | At least 90% |
| Recall for direct-address moments | At least 80% |
| False alerts | At most 2 per call hour |
| End-of-question to visible alert latency, p95 | At most 3 seconds |
| Duplicate alerts | Less than 1% |
| One-week retention | Measure during beta; target at least 70% |

These are proposed release targets. They must not be reported as achieved until supported by evaluation results.

Precision and recall must be measured independently. Reducing the number of alerts is not a valid improvement if the system simply stops detecting questions.

### Definition of an Actionable Alert

An alert is actionable when:

1. A question or request is reasonably likely to be directed at the user.
2. The original question or request can be recovered accurately enough to be useful.
3. The alert arrives while responding is still relevant.
4. The same conversational moment has not already triggered an alert.

---

## 2. Scope

### Included in the MVP

- Windows desktop application.
- System audio loopback and microphone capture.
- Streaming speech-to-text.
- Rolling 60–90 second transcript buffer.
- Name-variant matching.
- Question and request candidate detection.
- LLM intent classification for ambiguous cases.
- Short Asked and Context summaries.
- Desktop overlay and optional sound.
- Visible listening indicator and pause/stop controls.
- Basic settings.
- Evaluation scripts and real-call testing.

### Excluded from the MVP

- Mobile call-audio capture.
- Mobile push notifications.
- User accounts and billing.
- Persistent transcript history.
- Broad multilingual support.
- Multi-provider production routing.
- macOS support before Windows feasibility is proven.

---

## 3. Architecture and Data Flow

```text
Windows System Audio + Microphone
                 |
                 v
Desktop Audio Capture and Resampling
                 |
                 v
Audio WebSocket
                 |
                 v
FastAPI Session Manager
                 |
                 v
Streaming Speech-to-Text
                 |
                 v
Final Transcript Segments
                 |
                 v
Rolling Transcript Buffer
                 |
                 v
Cheap Candidate Checks
                 |
          +------+------+
          |             |
       Clear Case   Ambiguous Case
          |             |
          |       Fast LLM Classifier
          +------+------+
                 |
                 v
Confidence + Freshness + Deduplication
                 |
                 v
Summary Generation and Validation
                 |
                 v
Alert Event over Event WebSocket
                 |
                 v
Desktop Overlay + Optional Sound
```

The backend should run locally during initial development and bind to `127.0.0.1`.

External provider requests use encrypted connections. The desktop frontend must not contain STT or LLM API keys.

### Audio Capture Requirements

- Capture system playback and microphone audio as separate streams where possible.
- Preserve source labels throughout the pipeline.
- Resample only when required by the STT provider.
- Begin testing with 100–250 ms audio chunks.
- Validate audio quality, routing, and end-to-end latency on actual calls.
- Test with headphones and different output configurations.
- Do not assume that system loopback contains only the remote caller.

Speaker diarization labels do not prove which speaker is the user. Local and remote audio may overlap or echo into one another.

---

## 4. Component Responsibilities

| File | Responsibility |
|---|---|
| `backend/app/main.py` | FastAPI lifecycle, HTTP endpoints, WebSocket connections |
| `backend/app/schemas.py` | Pydantic models and shared event contracts |
| `backend/app/stt.py` | Streaming STT adapter and transcript segment handling |
| `backend/app/buffer.py` | Rolling transcript buffer and session cleanup |
| `backend/app/triggers.py` | Candidate detection, name matching, confidence and cooldown |
| `backend/app/summarizer.py` | Generate and validate Asked and Context |
| `backend/app/alerts.py` | Dispatch events to connected desktop clients |
| `prototypes/capture_win.py` | Standalone Windows capture experiment |
| `prototypes/stt_stream.py` | Streaming STT and latency experiment |
| `desktop/src/` | React interface, settings, status, and alert overlay |
| `desktop/src-tauri/` | Native integration, permissions, tray, and packaging |
| `eval/evaluate.py` | Precision, recall, false alerts/hour, and latency reporting |

Provider-specific functionality should be isolated behind adapters so that changing a provider does not require rewriting the entire pipeline.

---

## 5. API and Message Contracts

### 5.1 HTTP Endpoints

- `POST /session/start` — create a new listening session.
- `POST /session/stop` — stop processing, close streams, and clear transient state.
- `GET /health` — return backend health information.
- `WS /audio` — receive binary audio chunks with source metadata.
- `WS /events` — deliver alert and session-status events.

Each session must have a unique identifier. Both WebSocket connections must be associated with the same active session.

Validate session state, message sizes, connection lifecycle, and ownership. Do not expose an unauthenticated audio-ingest service publicly.

### 5.2 Audio Chunk Contract

Suggested metadata:

```json
{
  "type": "audio_chunk",
  "session_id": "session-id",
  "source": "loopback",
  "sequence": 42,
  "sample_rate": 16000,
  "channels": 1,
  "encoding": "pcm_s16le"
}
```

Send PCM audio as binary WebSocket frames rather than base64-encoded JSON.

The implementation team must agree on the exact framing protocol before integrating the desktop and backend. Metadata must be associated unambiguously with each chunk.

The sample rate and encoding above are proposed defaults. Confirm the provider's supported format before implementation.

### 5.3 Stable Alert Event Schema

Do not change this schema without coordinating with the team.

```json
{
  "type": "alert",
  "schema_version": 1,
  "timestamp": "2026-10-18T19:00:00Z",
  "session_id": "session-id",
  "event_id": "unique-event-id",
  "trigger": "name_mention",
  "confidence": 0.92,
  "asked": "Can you share the status of the API work?",
  "context": "The team is discussing delays in the API migration and the release plan.",
  "speaker": "Speaker 2"
}
```

#### Field rules

- `type`: must be `alert`.
- `schema_version`: integer identifying the contract version.
- `timestamp`: ISO 8601 UTC timestamp.
- `session_id`: active session identifier.
- `event_id`: unique event identifier for deduplication.
- `trigger`: one of `name_mention`, `question_pause`, or `llm_intent`.
- `confidence`: number between 0 and 1.
- `asked`: maximum 20 words.
- `context`: maximum 25 words.
- `speaker`: speaker label when available; otherwise null or unknown.

Never invent a speaker identity. If the schema changes, increment its version and update the desktop and backend together.

Session-status events should be defined separately for states such as `listening`, `paused`, `stopped`, `reconnecting`, and `error`.

---

## 6. Trigger Engine

The trigger engine must prioritize inexpensive checks and call the LLM only when necessary.

### Step 1: Name-Variant Matching

Maintain a user-configured list of names, nicknames, and common transcription variants.

- Normalize transcript text before matching.
- Support fuzzy and optionally phonetic matching.
- Test recognition errors involving Indian names and accents.
- Avoid accidental matches inside unrelated words.
- Treat fuzzy matches as candidate evidence rather than unquestionable proof.
- Do not assume a name mention automatically means the user is being addressed.

### Step 2: Question and Request Detection

Detect likely direct questions and requests, including statements such as:

- "Can you share the status?"
- "Could you take the next action?"
- "Please send the update."
- "What do you think about this approach?"

A question followed by more than 1.5 seconds of silence while the user's microphone is silent may support a candidate decision.

A pause alone must never establish that the question was directed at the user.

### Step 3: Context-Aware Intent Classification

For ambiguous cases, pass the minimum relevant transcript context to a fast LLM.

Suggested structured output:

```json
{
  "directed": true,
  "confidence": 0.86,
  "reason": "The speaker named the user and requested a status update."
}
```

The `reason` field is intended for internal evaluation and debugging, not for displaying hidden model reasoning to users.

Requirements:

- Validate the output schema.
- Apply a strict timeout.
- Handle malformed responses and provider failures.
- Avoid sending the entire meeting transcript when a shorter window is sufficient.
- Treat transcript content as untrusted input.
- Define safe fallback behavior when classification fails.

### Step 4: Confidence, Freshness, and Deduplication

- Suppress repeated alerts for the same conversational moment.
- Begin with a 20-second cooldown for ordinary alerts.
- Permit bypass only for clearly distinct, high-confidence events under a bounded rule.
- Drop stale alerts when the conversation has moved on.
- Do not queue old alerts for later display as if they were current.

Tune thresholds against the evaluation dataset rather than selecting them solely by intuition.

---

## 7. Summarizer

The summarizer generates a short context-recovery alert. It must not answer the user's question on their behalf.

### Prompt

```text
You are generating a short context-recovery alert for a live call.

Use only the supplied transcript. Do not invent facts, names, deadlines,
commitments, or decisions.

If the question or request cannot be recovered reliably, return an
explicit failure status instead of guessing.

Return valid JSON:
{
  "asked": "The exact question/request directed at the user, at most 20 words",
  "context": "The relevant discussion context, at most 25 words"
}
```

### Validation Requirements

- Prefer the original question wording over a paraphrase.
- Enforce the word limits.
- Validate the JSON structure.
- Handle provider timeouts and malformed responses.
- Escape output before rendering it in the UI.
- Never allow transcript text to override application instructions.
- Suppress unreliable alerts rather than fabricating content.

Summary generation may run in parallel with the final intent decision when appropriate, but the app must not show an alert until it has sufficient evidence that the event is relevant.

---

## 8. Latency Budget

Measure latency from the end of the question to the moment the alert becomes visible.

Initial planning estimates:

| Stage | Initial budget |
|---|---:|
| STT finalization and endpointing | 0.8–1.4 seconds |
| Candidate decision | 0.1–0.4 seconds |
| LLM decision and summary, when needed | 0.3–0.9 seconds |
| Event transport and UI render | 0.1–0.2 seconds |

These ranges can add up to more than three seconds. They are hypotheses to measure, not guarantees.

Record timestamps for:

- Audio capture.
- Transcript finalization.
- Candidate creation.
- Intent decision.
- Summary completion.
- Alert transmission.
- Overlay rendering.

Report median and p95 latency and the percentage of alerts exceeding three seconds.

Possible optimizations include partial-transcript processing, parallel operations, shorter prompts, and fewer LLM calls. Do not sacrifice correctness just to show an earlier alert.

---

## 9. Desktop UI Requirements

### Application States

- `stopped`: no capture or processing.
- `starting`: permissions and streams are being initialized.
- `listening`: persistent listening indicator is visible.
- `paused`: capture and processing are paused.
- `reconnecting`: temporary connection failure.
- `error`: actionable error with a safe stopped state when necessary.

### MVP Controls

- Start, pause, stop, and quit.
- Persistent listening indicator.
- Compact always-on-top alert overlay.
- Optional sound.
- User name variants.
- Sensitivity setting.
- Keyboard shortcut.
- Dismissible alert.
- Clear microphone, system-audio, backend, and provider error messages.

The overlay should not unnecessarily steal focus or interfere with typing. Click-through behavior must not prevent dismissal or access to essential controls.

---

## 10. Privacy and Security

- Require explicit opt-in before capturing audio.
- Keep the listening indicator visible while capture is active.
- Provide immediate pause and stop controls.
- Do not retain raw audio by default.
- Keep transcript state bounded to 60–90 seconds.
- Clear transient transcript data at session end.
- Keep API keys on the backend.
- Bind local development services to `127.0.0.1`.
- Validate session state, message sizes, and WebSocket connections.
- Use TLS for remote provider connections.
- Document which data is sent to each provider.
- Review provider retention settings and terms.
- Avoid logging raw audio and unnecessary transcript content.
- Review applicable consent laws, workplace policies, and privacy obligations before release.

Callrizer must not be presented as a covert recording tool or as a way to bypass call-platform protections.

---

## 11. Evaluation Plan

Create a labeled dataset with at least 100 scenarios for the initial iteration, then expand it. Use appropriately consented recordings or constructed test conversations.

Include:

1. Name mention followed by a direct question.
2. Direct question without a name mention.
3. Question directed at another participant.
4. Name mention that is not an address.
5. Rhetorical question.
6. Request phrased as a statement.
7. Multiple speakers talking over one another.
8. Noisy audio and different accents.
9. Incorrect transcription of the user's name.
10. User has already answered or the question has become stale.

For each scenario, label whether the user was addressed, the relevant question span, and whether an alert should occur.

### Metrics

Precision = true alerts / all alerts.

Recall = true alerts / all actual direct-address moments.

Also measure:

- False alerts per call hour.
- Missed direct-address moments.
- Median and p95 end-to-end latency.
- Duplicate-alert rate.
- Performance by scenario and audio condition.

Keep a held-out test set for final measurements. Clearly report any limitations in the dataset.

---

## 12. Development Phases

### Phase 0 — Feasibility (Week 1)

- [ ] Build a standalone Windows system-audio capture prototype.
- [ ] Capture microphone audio separately.
- [ ] Test on a real supported call application with appropriate consent.
- [ ] Verify audio routing and source separation for the tested configuration.
- [ ] Test streaming STT.
- [ ] Measure transcription latency.
- [ ] Document device and permission limitations.

**Gate:** Do not proceed to full integration until capture and transcription are sufficiently reliable for the target setup.

### Phase 1 — End-to-End Skeleton (Weeks 2–3)

- [ ] Create FastAPI session endpoints and WebSockets.
- [ ] Define shared Pydantic schemas.
- [ ] Implement the rolling transcript buffer.
- [ ] Add name-mention candidate detection.
- [ ] Implement summary generation and validation.
- [ ] Build a desktop overlay using a hard-coded fake alert.
- [ ] Connect real backend events to the overlay.
- [ ] Demonstrate the full pipeline on a real call.

### Phase 2 — Accuracy (Week 4)

- [ ] Add question/request candidate detection.
- [ ] Add LLM intent classification for ambiguous cases.
- [ ] Implement cooldown, deduplication, and stale-event suppression.
- [ ] Create and label the evaluation dataset.
- [ ] Measure precision, recall, false alerts/hour, and latency.
- [ ] Fix the most frequent failure modes.

### Phase 3 — Beta Readiness (Weeks 5–6)

- [ ] Add settings and keyboard controls.
- [ ] Add consent and privacy UX.
- [ ] Harden connection recovery and error handling.
- [ ] Package the Windows application.
- [ ] Test with 5–10 target users.
- [ ] Measure repeated usage and willingness to pay.
- [ ] Decide whether to improve, narrow the use case, or expand.

Do not add mobile push, billing, or macOS support until the Windows workflow has passed its validation gates.

---

## 13. Team Ownership

| Owner | Responsibility | Primary folders |
|---|---|---|
| A — Audio/Desktop | Capture, native integration, overlay, packaging | `desktop/`, `prototypes/` |
| B — AI Pipeline | STT, buffer, triggers, summarizer, latency | `backend/` |
| C — Product/QA | UX collaboration, consent, test scenarios, evaluation | `eval/`, `docs/` |

### Git Workflow

- Keep `main` buildable.
- Use branches such as `feat/audio-capture`, `feat/stt-stream`, and `feat/alert-overlay`.
- Keep pull requests focused.
- Require at least one teammate review.
- Update this document before changing shared contracts.
- Never commit `.env`, API keys, private transcripts, or call recordings.
- Test integrated changes on real calls with appropriate consent.

---

## 14. Definition of Done

The MVP is ready for a limited beta when:

- The user can explicitly start, pause, and stop listening.
- The listening state remains visible while capture is active.
- The supported Windows configurations capture audio reliably enough for the tested use case.
- The end-to-end audio-to-alert flow works on real calls.
- The alert schema is validated and shared across frontend and backend.
- The evaluation report includes precision, recall, false alerts/hour, and p95 latency.
- Session stop closes connections and clears transient transcript state.
- API keys are not shipped in the desktop bundle or repository.
- Consent and privacy documentation are available to beta users.
- Any unmet release target is explicitly documented.

---

## 15. Open Decisions

Update this section as the team gathers evidence.

- Final Windows capture implementation and supported device configurations.
- Whether provider diarization is sufficient for the target calls.
- Final STT and LLM provider selection.
- Confidence thresholds and cooldown values based on evaluation.
- Whether local inference is feasible without unacceptable latency or accuracy loss.
- macOS implementation after Windows validation.
- License before public release.