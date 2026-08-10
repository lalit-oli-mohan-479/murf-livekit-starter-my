# Aarav — Indian Financial Literacy Voice Agent 🇮🇳
> **Built for #10DaysOfVoiceAgents Challenge by Murf AI**  
> Powered by **Murf Falcon TTS** (Fastest Streaming Voice API), **LiveKit Agents**, **Deepgram STT**, & **Google Gemini LLM**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming) [![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io) [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

---

## 🌟 What We Have Built (Days 1 – 5 Progress)

Aarav is a friendly, register-aware, and culturally sensitive digital financial guide working for **Jan Dhan Seva** (National Financial Literacy Campaign). He helps common citizens understand basic banking, fixed deposits, social security schemes, and live market rates in **Hindi, English, and Hinglish**.

```
User speaks → [Deepgram STT] → text → [Gemini LLM] → response → [Murf Falcon TTS] → audio → User hears
                                           ↓
                              [Tools & SQLite Memory] → [LiveKit Data Channel] → 📱 UI Card Push
```

---

### 📅 Feature Roadmap & Achievements

#### 🔹 Day 1 — Pipeline & Foundations
- Configured real-time WebRTC audio transport using **LiveKit**.
- Integrated **Deepgram STT** (`nova-3`), **Google Gemini LLM**, and **Murf Falcon TTS** (using the `Samar` voice model).
- Established ultra-low latency streaming voice loop (<300ms total pipeline).

#### 🔹 Day 2 — Persona & Safety Guardrails
- Created the **Aarav** persona: patient, warm financial literacy educator.
- Implemented **Strict Language & Script Mirroring**:
  - Devanagari Hindi input → Pure Devanagari Hindi output.
  - English input → Pure English output.
  - Hinglish input → Script-sensitive response in Devanagari Hindi.
- Built **Financial Safety Guardrails**:
  - Automatically intercepts requests for PINs, passwords, OTPs, or bank account numbers and issues safety warnings.
  - Escalates transaction/complaint requests to official bank helplines (1915).

#### 🔹 Day 3 — Frontend Customization & Visualizers
- Customized the Next.js frontend with live **bilingual chat transcripts**.
- Added real-time speaker state indicators (`Listening`, `Thinking`, `Speaking`).
- Integrated dynamic wave audio visualizers and session control bars (`AgentControlBar`).

#### 🔹 Day 4 — Persistent Agent Memory & Consent
- Integrated local **SQLite database** (`db.py`) for persistent caller profile memory.
- **Explicit Consent Flow**: Aarav explicitly recaps details (name, language, topic) and asks for permission before saving user records.
- **Returning User Recognition**: Greets returning callers by name and references their previous interaction date.
- **"Forget Me" Feature**: Users can request data deletion at any time via `forget_caller`.

#### 🔹 Day 5 — Real-Time Tools, Data Sources & UI Push
- **Live Bullion Rate Tool (`get_gold_silver_price`)**:
  - Fetches live 24K and 22K Gold & Silver rates in INR per gram using **GoldAPI.io**.
  - **Graceful Failure**: If the API times out or fails, Aarav speaks fallback estimated market ranges and directs users to check locally instead of going silent or hallucinating.
- **Government Scheme Lookup (`lookup_govt_scheme`)**:
  - Curated local dataset (`schemes_data.json`) covering 8 major Indian schemes (*Jan Dhan Yojana, Atal Pension Yojana, PM Suraksha Bima, PM Jeevan Jyoti Bima, Sukanya Samriddhi, PM Kisan, PM Mudra Yojana, Stand-Up India*).
  - Provides required document checklists, eligibility, benefits, and official portal links (`myscheme.gov.in`).
- **FD Returns Calculator (`calculate_fd_returns`)**:
  - Computes maturity and interest earned using current SBI FD rates (7.1% p.a., August 2026). Always speaks rate source and date.
- **Tool Chaining (Advanced)**:
  - Reuses saved user facts (age, name) from Day 4 memory inside scheme eligibility tools without re-asking questions.
- **Real-Time UI Data Push (Advanced)**:
  - Pushes structured JSON tool outputs over LiveKit Data Channels to display floating, interactive cards (`ToolDataCard`) on screen showing live rates, document checkmarks (`✓ Aadhaar Card`), and FD maturity breakdowns!

---

## 🛠️ Data Sources & Freshness Documentation

| Tool | Data Source | Live / Local | Verification Date / API |
|---|---|---|---|
| `get_gold_silver_price` | [GoldAPI.io](https://www.goldapi.io/) | **Live API** | Real-time live market timestamp |
| `lookup_govt_scheme` | Curated dataset (`schemes_data.json`) | **Local** | Verified August 2026 from official govt portals |
| `calculate_fd_returns` | SBI General Citizen FD Rate | **Local** | 7.1% p.a., August 2026 |
| `lookup_caller` / `save_caller_info` | SQLite Database (`backend/src/agent_memory.db`) | **Local** | Real-time caller profile storage |

> **Note on Government Scheme Data:** There is currently no open public API for Indian government schemes (`myscheme.gov.in` does not provide a public API). Therefore, scheme information is stored locally in `backend/src/schemes_data.json` based on official government documentation.

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
- **Python 3.10+** & **[uv](https://docs.astral.sh/uv/)**
- **Node.js 18+** & **pnpm**
- **LiveKit Cloud** account (or local `livekit-server`)

### 1. Clone the repository
```bash
git clone https://github.com/murf-ai/murf-livekit-starter.git
cd murf-livekit-starter
```

### 2. Configure Environment Variables
Create `.env.local` in `backend/` and `frontend/`:

**`backend/.env.local`**:
```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
MURF_API_KEY=your_murf_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
GOOGLE_API_KEY=your_google_gemini_api_key
GOLD_API_KEY=your_goldapi_key  # Optional: for live gold rates
```

### 3. Install Dependencies & Run

**Option A — Windows PowerShell (All-in-one):**
```powershell
.\start_app.ps1
```

**Option B — Separate Terminals:**
```bash
# Terminal 1 — LiveKit Server
livekit-server --dev

# Terminal 2 — Backend Agent
cd backend
uv sync
uv run python src/agent.py dev

# Terminal 3 — Frontend UI
cd frontend
pnpm install
pnpm dev
```

Open **`http://localhost:3000`** in your browser, click **"START TALKING"**, and start conversing with Aarav!

---

## 📸 Demo Queries to Try

- 🪙 **Live Gold Price:** *"Aaj gold price kya hai?"* → Aarav speaks rates + Live Bullion Card pops up!
- 📄 **Government Scheme:** *"Sukanya Samriddhi Yojana ke documents batao."* → Document checklist card appears!
- 💰 **FD Calculator:** *"50,000 Rupees par 2 saal ka FD return calculate karo."* → Maturity breakdown card appears!
- 🔗 **Tool Chaining:** Tell Aarav your age, then ask *"Kya main Atal Pension Yojana ke liye eligible hoon?"* → Aarav checks eligibility without re-asking age!

---

## 🔗 Links & Resources

- [Murf API Documentation](https://murf.ai/api/docs)
- [LiveKit Agents Framework](https://docs.livekit.io/agents)
- [Deepgram STT Docs](https://developers.deepgram.com)
- [GoldAPI.io](https://www.goldapi.io/)

---

## 📜 License
MIT License
