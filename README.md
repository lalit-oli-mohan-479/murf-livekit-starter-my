# Aarav — Indian Financial Literacy Voice Agent 🇮🇳
> **Built for #10DaysOfVoiceAgents Challenge by Murf AI**  
> Powered by **Murf Falcon TTS** (Fastest Streaming Voice API), **LiveKit Agents**, **Deepgram STT**, & **Google Gemini LLM**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming) [![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io) [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

---

## 🌟 What We Have Built (Days 1 – 7 Progress)

Aarav is a friendly, register-aware, and culturally sensitive digital financial guide working for **Jan Dhan Seva** (National Financial Literacy Campaign). He helps common citizens understand basic banking, fixed deposits, social security schemes, and live market rates in **Hindi, English, and Hinglish**, places proactive outbound SIP reminder calls, and seamlessly escalates complex disputes & cyber fraud claims to human support desks with SQLite persistence and real-time portal tracking!

```
Inbound Flow:  User speaks → [Deepgram STT] → text → [Gemini LLM] → response → [Murf Falcon TTS] → audio → User hears
                                            ↓
                               [Tools & SQLite Memory] → [LiveKit Data Channel] → 📱 UI Card Push

Escalation:   High-Risk Claim → [Explicit Consent] → [PII Redaction] → [SQLite Ticket ESC-XXXXX] → 📋 Support Portal & Webhook

Outbound Flow: [CSV Batch / CLI] → [LiveKit SIP Trunk] → 📞 Callee Phone → [Gated Identity Gate] → 📊 [SQLite Call Log & Retry]
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

#### 🔹 Day 6 — Outbound SIP Telephony Agent & Outcome Handling 📞
- **Outbound Telephony & SIP Trunking**:
  - Configured LiveKit Outbound SIP trunking with Linphone to place real outbound phone calls.
- **Gated Identity Verification (Security Gate)**:
  - Verified caller identity (*"नमस्ते, मैं आरव बोल रहा हूँ... क्या मैं Ramesh जी से बात कर रहा हूँ?"*). If identity is denied, Aarav apologizes (`wrong_person_reached`) and disconnects immediately.
- **CSV Batch Campaign Management**:
  - Added support for loading target phone numbers, customer names, scheme details, and application deadlines directly from CSV files (`customers.csv`).
- **Telephony Outcome Engine & Retry Logic**:
  - Defined outcome handling for `NO_ANSWER`, `BUSY`, `VOICEMAIL`, `WRONG_PERSON`, `EARLY_HANGUP`, and `COMPLETED` with automated retry recommendations.
- **SQLite Audit & Duration Persistence**:
  - Automatically records call telemetry into SQLite (`data.db` -> table `outbound_calls`), tracking recipient details, exact call duration in seconds, outcome status, and retry recommendations.

#### 🔹 Day 7 — Human Escalation Protocol, SQLite Ticket Tracking & Support Portal 🛡️
- **Human Escalation System (`create_escalation`)**:
  - Automatically handles high-risk financial disputes, unauthorized cyber fraud claims, and complex account freeze issues by generating unique Reference IDs (e.g. `ESC-34036`).
- **Mandatory Consent & PII Redaction**:
  - Enforces explicit consent asking before escalating and automatically redacts passwords, OTPs, PINs, or 16-digit card numbers.
- **Voice Ticket Status Lookup (`check_escalation_status`)**:
  - Allows callers to query their escalation status directly over voice (e.g., *"ESC-34036 ka status kya hai?"*).
- **Web Complaint Support Portal & API**:
  - Added Next.js 15 API (`/api/escalations`) and an interactive **Jan Dhan Support & Escalation Portal** modal with reference ID search and visual AI Non-Decision Boundary documentation.
- **Background Discord Webhook Integration**:
  - Asynchronously posts rich embed alerts to Discord support channels without blocking the voice agent's event loop.

---

## 🛠️ Data Sources & Freshness Documentation

| Tool | Data Source | Live / Local | Verification Date / API |
|---|---|---|---|
| `get_gold_silver_price` | [GoldAPI.io](https://www.goldapi.io/) | **Live API** | Real-time live market timestamp |
| `lookup_govt_scheme` | Curated dataset (`schemes_data.json`) | **Local** | Verified August 2026 from official govt portals |
| `calculate_fd_returns` | SBI General Citizen FD Rate | **Local** | 7.1% p.a., August 2026 |
| `lookup_caller` / `save_caller_info` | SQLite Database (`backend/src/data.db`) | **Local** | Real-time caller profile storage |
| `log_outbound_call` | SQLite Database (`backend/src/data.db`) | **Local** | Outbound call duration & outcome audit |

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
- **Python 3.10+** & **[uv](https://docs.astral.sh/uv/)**
- **Node.js 18+** & **pnpm**
- **LiveKit Cloud** account

---

### 1. Inbound Web Agent Quickstart

```bash
# Terminal 1 — Backend Agent
cd backend
uv sync
uv run python src/agent.py dev

# Terminal 2 — Frontend UI
cd frontend
pnpm install
pnpm dev
```
Open **`http://localhost:3000`** in your browser, click **"START TALKING"**, and start conversing with Aarav!

---

### 2. Outbound Telephony Agent (Day 6) Quickstart

```bash
# Terminal 1 — Outbound Agent Worker
cd backend
uv run python src/telephony/outbound/agent.py dev

# Terminal 2 — Dispatch Outbound Call from CSV Batch
cd backend
uv run python src/telephony/outbound/dial.py --csv src/telephony/outbound/customers.csv --row 3
```

---

## 📸 Demo Queries & Test Scenarios

### Inbound Queries:
- 🪙 **Live Gold Price:** *"Aaj gold price kya hai?"* → Aarav speaks rates + Live Bullion Card pops up!
- 📄 **Government Scheme:** *"Sukanya Samriddhi Yojana ke documents batao."* → Document checklist card appears!
- 💰 **FD Calculator:** *"50,000 Rupees par 2 saal ka FD return calculate karo."* → Maturity breakdown card appears!

### Outbound Call Scenarios (Day 6):
- 🆔 **Identity Verification:** Confirm name (*"हाँ, मैं ललित बात कर रहा हूँ"*) -> Aarav proceeds to disclose scheme details.
- 🚫 **Wrong Person Gate:** Deny name (*"नहीं, गलत नंबर है"*) -> Aarav apologizes and hangs up automatically.
- 🔒 **Security Guardrail:** Ask to share OTP/PIN -> Aarav refuses and states security warning.
- 📊 **SQLite Audit Log:** Disconnect call -> Watch terminal print `[CALL OUTCOME REPORT (SAVED TO SQLITE)]` with call duration & outcome status.

---

## 🔗 Links & Resources

- [Murf API Documentation](https://murf.ai/api/docs)
- [LiveKit Agents Framework](https://docs.livekit.io/agents)
- [Deepgram STT Docs](https://developers.deepgram.com)
- [GoldAPI.io](https://www.goldapi.io/)

---

## 📜 License
MIT License
