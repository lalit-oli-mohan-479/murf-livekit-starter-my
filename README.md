# Multilingual AI Financial Voice Assistant 🇮🇳
> **Built for #10DaysOfAIVoiceAgents Challenge by Murf AI**  
> Powered by **Murf Falcon TTS** (Fastest Streaming Voice API), **LiveKit Agents**, **Deepgram STT**, & **Google Gemini LLM**.

[![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming) [![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io) [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

## 🌟 What We Have Built (Days 1 – 10 Completed)

Aarav is a friendly, register-aware, and culturally sensitive digital financial guide working for **Jan Dhan Seva** (National Financial Literacy Campaign). He operates as a **Multi-Agent Voice Mesh** with 4 specialized AI personas, helping common citizens understand basic banking, fixed deposits, social security schemes, and live market rates in **Hindi, English, and Hinglish**, placing proactive outbound SIP reminder calls, seamlessly transferring callers to domain specialists (**Kavya, Vikram, Kirti**), escalating complex disputes & cyber fraud claims to human support desks, and providing operational visibility via a real-time **Call Analytics Dashboard** with SQLite persistence!

### 📅 Feature Roadmap

- **Day 1:** LiveKit, Deepgram STT, Gemini LLM, and Murf Falcon TTS pipeline.
- **Day 2:** Aarav persona, multilingual/script-aware responses, and financial safety guardrails.
- **Day 3:** Next.js bilingual transcripts, speaker states, and audio visualizers.
- **Day 4:** SQLite caller memory, explicit consent, returning-user recognition, and Forget Me.
- **Day 5:** Live gold/silver rates, government scheme lookup, FD calculator, tool chaining, and UI data cards.
- **Day 6:** Outbound SIP calls, identity gate, CSV campaigns, retry logic, and SQLite call audit.
- **Day 7:** Human escalation, consent, PII redaction, ticket status, support portal, and webhook alerts.
- **Day 8:** Call analytics dashboard, success/failure tracking, latency metrics, charts, and filters.
- **Day 9:** Four-agent specialist mesh and real-time TTS voice switching.
- **Day 10:** Technical journey, architecture documentation, and challenge completion.

## 🚀 Quickstart

### Prerequisites
- Python 3.10+ & [uv](https://docs.astral.sh/uv/)
- Node.js 18+ & pnpm
- LiveKit Cloud account

### Inbound Web Agent
```bash
cd backend
uv sync
uv run python src/agent.py dev

cd ../frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000` and click **START TALKING**.

### Outbound Telephony Agent
```bash
cd backend
uv run python src/telephony/outbound/agent.py dev
uv run python src/telephony/outbound/dial.py --csv src/telephony/outbound/customers.csv --row 3
```

## 🔗 Links & Resources
- [Murf API Documentation](https://murf.ai/api/docs)
- [LiveKit Agents Framework](https://docs.livekit.io/agents)
- [Deepgram STT Docs](https://developers.deepgram.com)
- [GoldAPI.io](https://www.goldapi.io/)
