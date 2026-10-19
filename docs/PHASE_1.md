# Phase 1: Desktop App & Python Backend Foundation

## 🎯 Objectives

Establish a reliable desktop application container (Tauri) paired with a local Python backend (FastAPI), including inter-process communication, connection lifecycle management, health monitoring, and shared schemas.

---

## 🏗️ Architecture Overview

```
+-------------------------------------------------------------+
|                     Tauri Desktop Shell                     |
|  +-------------------------------------------------------+  |
|  |                 Frontend (React / Vite)               |  |
|  |  - Components (Header, StatusBadge, LogViewer)        |  |
|  |  - Pages (Dashboard, Settings)                        |  |
|  |  - Services (BackendClient, WebSocketClient)          |  |
|  +-------------------------------------------------------+  |
|                             |                               |
|              Tauri Rust Core (Process Manager)              |
+-----------------------------+-------------------------------+
                              | HTTP / WebSocket (localhost)
+-----------------------------v-------------------------------+
|                       Python Backend                        |
|  - FastAPI HTTP routes (/health, /api/status, /api/config)  |
|  - WebSocket server (/ws/events, /ws/stream)                |
|  - Pydantic schemas (backend/schemas & shared/schemas)      |
+-------------------------------------------------------------+
```

---

## 📋 Implementation Checklist

### 1. Python Backend
- [ ] Initialize FastAPI application in `backend/api/main.py`.
- [ ] Implement core configuration loader in `backend/core/config.py` using `.env`.
- [ ] Add health check endpoint (`GET /health`) returning backend version and status.
- [ ] Implement WebSocket endpoint (`/ws/events`) for bi-directional live communication.
- [ ] Implement automated unit test suite in `backend/tests/unit/test_health.py`.

### 2. Desktop Frontend (Tauri)
- [ ] Configure Tauri app in `desktop/src-tauri`.
- [ ] Set up frontend router and core layout in `desktop/src/pages` and `desktop/src/components`.
- [ ] Implement `BackendClient` in `desktop/src/services/api.ts` for HTTP requests.
- [ ] Implement WebSocket reconnecting listener in `desktop/src/services/websocket.ts`.
- [ ] Add backend status indicator in the UI (Connected, Disconnected, Connecting).

### 3. Shared Schemas
- [ ] Define standardized event and message contracts in `shared/schemas/`.
- [ ] Validate request/response payloads on both sides.

---

## ✅ Acceptance Criteria

1. Running `npm run tauri dev` boots the desktop app with no console errors.
2. The UI displays an active green status indicator when the Python backend is running.
3. If the backend is shut down, the UI gracefully transitions to "Disconnected" and attempts reconnection.
4. `pytest backend/tests/unit` passes with 100% success rate.
