# Multilingual AI Financial Voice Assistant 🇮🇳
> **Built for #10DaysOfAIVoiceAgents Challenge by Murf AI**  
> Powered by **Murf Falcon TTS** (Fastest Streaming Voice API), **LiveKit Agents**, **Deepgram STT**, & **Google Gemini LLM**.

[![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming) [![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io) [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

## 🌟 What We Have Built (Days 1 – 10 Completed)

Aarav is a friendly, register-aware, and culturally sensitive digital financial guide working for **Jan Dhan Seva** (National Financial Literacy Campaign). He operates as a **Multi-Agent Voice Mesh** with 4 specialized AI personas, helping common citizens understand basic banking, fixed deposits, social security schemes, and live market rates in **Hindi, English, and Hinglish**, placing proactive outbound SIP reminder calls, seamlessly transferring callers to domain specialists (**Kavya, Vikram, Kirti**), escalating complex disputes & cyber fraud claims to human support desks, and providing operational visibility via a real-time **Call Analytics Dashboard** with SQLite persistence!

```
Inbound Flow:  User speaks → [Deepgram STT] → text → [Gemini LLM] → response → [Murf Falcon TTS] → audio → User hears
                                             ↓
                               [Tools & SQLite Memory] → [LiveKit Data Channel] → 📱 UI Card Push

Multi-Agent:   User query topic → [Handoff Tool] → [Atomic TTS Engine Switch] → 🎭 Specialist Speaks (Samar/Pooja/Nikhil/Palak)

Analytics:     Call Disconnect → [agent.py Listener] → [SQLite call_logs Table] → 📊 Live Dashboard & Donut Chart

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
- Implemented **Strict Language & Script Mirroring**.
- Built **Financial Safety Guardrails** for PINs, passwords, OTPs, and bank account numbers.

#### 🔹 Day 3 — Frontend Customization & Visualizers
- Customized the Next.js frontend with live **bilingual chat transcripts**.
- Added real-time speaker state indicators (`Listening`, `Thinking`, `Speaking`).
- Integrated dynamic wave audio visualizers and session control bars.

#### 🔹 Day 4 — Persistent Agent Memory & Consent
- Integrated local **SQLite database** for persistent caller profile memory.
- Added explicit consent before saving user records and a **Forget Me** feature.

#### 🔹 Day 5 — Real-Time Tools, Data Sources & UI Push
- Added live gold and silver rates, government scheme lookup, and FD returns calculation.
- Added tool chaining with saved caller facts.
- Added real-time structured UI cards over LiveKit Data Channels.

#### 🔹 Day 6 — Outbound SIP Telephony Agent & Outcome Handling 📞
- Configured LiveKit outbound SIP trunking with Linphone.
- Added gated identity verification, CSV campaign management, retry logic, and SQLite call auditing.

#### 🔹 Day 7 — Human Escalation Protocol & Support Portal 🛡️
- Added high-risk financial dispute and cyber-fraud escalation with unique reference IDs.
- Added mandatory consent, PII redaction, voice status lookup, support portal, API, and Discord webhook alerts.

#### 🔹 Day 8 — Call Analytics Dashboard 📊
- Added success/failure benchmarks and SQLite session-level disconnect logging.
- Added real-time call analytics, latency tracking, SVG donut chart, failure breakdown, and filters.

#### 🔹 Day 9 — Multi-Agent Mesh & Voice Engine Switching 🔄🎭
- Built the 4-agent specialist mesh: **Aarav, Kavya, Vikram, and Kirti**.
- Added real-time specialist handoffs and atomic TTS engine switching.
- Hardened tool integration and Gemini configuration.

#### 🔹 Day 10 — Share Your Voice Agent Journey 🚀
- Published the technical project journey and architecture documentation.
- Added visual system architecture and cover artwork.
- Shared the completed 10-day Jan Dhan Seva project journey.

---

## 🛠️ Data Sources & Freshness Documentation

| Tool | Data Source | Live / Local | Verification Date / API |
|---|---|---|---|
| `get_gold_silver_price` | GoldAPI.io | **Live API** | Real-time live market timestamp |
| `lookup_govt_scheme` | Curated `schemes_data.json` | **Local** | Verified August 2026 |
| `calculate_fd_returns` | SBI FD Rate | **Local** | 7.1% p.a., August 2026 |
| `lookup_caller` / `save_caller_info` | SQLite Database | **Local** | Real-time caller profile storage |
| `log_outbound_call` | SQLite Database | **Local** | Outbound call duration & outcome audit |

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
- **Python 3.10+** & **[uv](https://docs.astral.sh/uv/)**
- **Node.js 18+** & **pnpm**
- **LiveKit Cloud** account

### Inbound Web Agent

```bash
cd backend
uv sync
uv run python src/agent.py dev

cd ../frontend
pnpm install
pnpm dev
```

Open **`http://localhost:3000`**, click **START TALKING**, and start conversing with Aarav.

### Outbound Telephony Agent

```bash
cd backend
uv run python src/telephony/outbound/agent.py dev
uv run python src/telephony/outbound/dial.py --csv src/telephony/outbound/customers.csv --row 3
```

---

## 📸 Demo Queries & Test Scenarios

- 🪙 **Live Gold Price:** *"Aaj gold price kya hai?"*
- 📄 **Government Scheme:** *"Sukanya Samriddhi Yojana ke documents batao."*
- 💰 **FD Calculator:** *"50,000 Rupees par 2 saal ka FD return calculate karo."*
- 🆔 **Identity Verification:** Confirm caller identity before disclosure.
- 🚫 **Wrong Person Gate:** Deny identity and the call disconnects.
- 🔒 **Security Guardrail:** Aarav refuses requests for OTP/PIN disclosure.

---

## 🔗 Links & Resources

- [Murf API Documentation](https://murf.ai/api/docs)
- [LiveKit Agents Framework](https://docs.livekit.io/agents)
- [Deepgram STT Docs](https://developers.deepgram.com)
- [GoldAPI.io](https://www.goldapi.io/)
