# Multilingual AI Financial Voice Assistant 🇮🇳

> Built for #10DaysOfAIVoiceAgents Challenge by Murf AI. Powered by Murf Falcon TTS, LiveKit Agents, Deepgram STT, and Google Gemini LLM.

## What We Have Built

Aarav is a multilingual financial literacy voice assistant for Jan Dhan Seva. The project combines a real-time voice pipeline, SQLite memory, financial tools, outbound SIP calling, human escalation, call analytics, and a multi-agent specialist mesh.

## Feature Roadmap

- **Day 1:** LiveKit + Deepgram + Gemini + Murf Falcon voice pipeline.
- **Day 2:** Aarav persona, multilingual responses, and financial safety guardrails.
- **Day 3:** Next.js bilingual transcripts, speaker states, and visualizers.
- **Day 4:** SQLite caller memory, consent, returning-user recognition, and Forget Me.
- **Day 5:** Gold/silver rates, government schemes, FD calculator, tool chaining, and UI cards.
- **Day 6:** Outbound SIP calls, identity verification, CSV campaigns, retry logic, and call auditing.
- **Day 7:** Human escalation, PII redaction, ticket tracking, support portal, and webhook alerts.
- **Day 8:** Call analytics dashboard, success/failure metrics, latency tracking, charts, and filters.
- **Day 9:** Four-agent specialist mesh and real-time TTS voice switching.
- **Day 10:** Technical journey, architecture documentation, and challenge completion.

## Quickstart

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

## Links

- [Murf API Documentation](https://murf.ai/api/docs)
- [LiveKit Agents](https://docs.livekit.io/agents)
- [Deepgram](https://developers.deepgram.com)
- [GoldAPI.io](https://www.goldapi.io/)
