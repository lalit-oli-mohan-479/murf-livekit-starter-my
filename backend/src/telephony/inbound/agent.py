"""Inbound telephony agent — answers incoming phone calls.

Callers dial your number, the SIP trunk routes it to LiveKit, and this agent
picks up and greets them.

Run with:

    uv run python src/telephony/inbound/agent.py dev

See src/telephony/README.md for trunk and dispatch rule setup.
"""

import logging
import os

from dotenv import load_dotenv
from livekit import api, rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("inbound-agent")

load_dotenv(".env.local")

TRANSFER_TO_NUMBER = os.getenv("TRANSFER_TO_NUMBER")

SYSTEM_PROMPT = """You are a helpful phone assistant. You answer incoming calls and help callers with their questions. You are on a phone call, so keep responses short and conversational — no formatting, emojis, or symbols. If the caller asks for a human, use the transfer_to_human tool. When the call is finished, use the end_call tool."""

GREETING = "Hello, thanks for calling. How can I help you today?"


def caller_phone_number(participant: rtc.RemoteParticipant) -> str | None:
    """Read the caller's phone number from SIP participant attributes."""
    if participant.kind != rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        return None
    return participant.attributes.get("sip.phoneNumber") or participant.identity


class InboundAgent(Agent):
    def __init__(self, ctx: JobContext) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.ctx = ctx

    @function_tool
    async def transfer_to_human(self, context: RunContext) -> str:
        """Transfer the caller to a human colleague.

        Use this when they explicitly ask for a person, or when you cannot help.
        """
        if not TRANSFER_TO_NUMBER:
            return "Transfers are not available. Offer to have someone call back."

        await context.session.generate_reply(
            instructions="Tell them you're connecting them to a colleague now."
        )

        logger.info("transferring call to %s", TRANSFER_TO_NUMBER)
        try:
            callee = None
            for p in self.ctx.room.remote_participants.values():
                callee = p.identity
                break

            if callee:
                await self.ctx.api.sip.transfer_sip_participant(
                    api.TransferSIPParticipantRequest(
                        room_name=self.ctx.room.name,
                        participant_identity=callee,
                        transfer_to=f"tel:{TRANSFER_TO_NUMBER}",
                        play_dialtone=True,
                    )
                )
        except Exception:
            logger.exception("transfer failed")
            return "The transfer did not go through. Apologize and offer a call back."

        return "Transferred."

    @function_tool
    async def end_call(self, context: RunContext) -> str:
        """Hang up the call once the conversation is finished."""
        await context.session.generate_reply(
            instructions="Thank them and say goodbye."
        )
        logger.info("ending call")
        await self.ctx.api.room.delete_room(
            api.DeleteRoomRequest(room=self.ctx.room.name)
        )
        return "Call ended."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="inbound-agent")
async def inbound_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="Samar",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=InboundAgent(ctx),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Greet the caller
    await session.say(GREETING, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
