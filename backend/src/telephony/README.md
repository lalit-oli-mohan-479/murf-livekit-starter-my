# Telephony — Inbound & Outbound Calls

Connect the voice agent to real phone numbers. Two starters:

- `inbound/` — someone calls your number, the agent answers
- `outbound/` — the agent calls someone

Both use the same voice pipeline as `src/agent.py` (Deepgram STT → Gemini → Murf Falcon TTS).

## Quick Start — Outbound with Linphone (Free)

### 1. Create a Linphone account
Go to [linphone.org](https://subscribe.linphone.org/register/email) and create an account.
Note your SIP username.

### 2. Create outbound trunk in LiveKit Cloud
In your [LiveKit Cloud dashboard](https://cloud.livekit.io/) → Telephony → SIP Trunks → Create outbound trunk:

```json
{
  "name": "linphone-trunk",
  "address": "sip.linphone.org",
  "transport": "SIP_TRANSPORT_TLS",
  "numbers": ["sip:<your-linphone-username>"]
}
```

Copy the trunk ID (starts with `ST_...`).

### 3. Add trunk ID to .env.local
```
LIVEKIT_SIP_OUTBOUND_TRUNK_ID=ST_your_trunk_id_here
```

### 4. Install Linphone app on your phone
- Download from App Store / Play Store
- Log in with your linphone.org credentials
- Settings → Calls → Advanced → Turn "Media encryption mandatory" **OFF**

### 5. Run the agent
```bash
# Terminal 1: Start the outbound agent worker
uv run python src/telephony/outbound/agent.py dev

# Terminal 2: Place a call
uv run python src/telephony/outbound/dial.py --to <your-linphone-username>
```

Your Linphone app will ring. Pick up and talk to Aarav!

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LIVEKIT_SIP_OUTBOUND_TRUNK_ID` | Yes (outbound) | Trunk ID from LiveKit Cloud |
| `TRANSFER_TO_NUMBER` | No | Phone number for human handoff |
