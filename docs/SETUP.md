# Setup Guide

This guide walks you through setting up your local development environment for **CallRizer**.

---

## 📋 Prerequisites

Before starting, ensure you have the following installed on your machine:

1. **Python 3.10+**:
   - Verify: `python --version`
2. **Node.js (LTS version 18+ or 20+) & npm**:
   - Verify: `node -v` and `npm -v`
3. **Rust Toolchain (for Tauri desktop app)**:
   - Install via [rustup.rs](https://rustup.rs/)
   - Verify: `rustc --version` and `cargo --version`
   - On Windows, ensure you have the **C++ Build Tools** installed via Visual Studio Installer.
4. **Git**:
   - Verify: `git --version`

---

## ⚙️ Step-by-Step Installation

### 1. Environment Configuration

Copy the template environment file to `.env`:

```bash
cp .env.example .env
```

Adjust any environment variables inside `.env` as needed (e.g. backend host, port, Whisper model size).

---

### 2. Python Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

3. Install backend dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Verify backend installation:
   ```bash
   pytest backend/tests/unit
   ```

---

### 3. Desktop App Setup (Tauri + Frontend)

1. Navigate to the `desktop` directory:
   ```bash
   cd desktop
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Run the desktop application in development mode:
   ```bash
   npm run tauri dev
   ```

---

## 🏃 Running the Full System Locally

For day-to-day development:

1. **Terminal 1 (Backend)**:
   ```bash
   .\venv\Scripts\activate
   uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - Swagger / OpenAPI Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

2. **Terminal 2 (Desktop)**:
   ```bash
   cd desktop
   npm run tauri dev
   ```
