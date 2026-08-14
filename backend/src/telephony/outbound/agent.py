"""Outbound telephony agent — Aarav calls citizens about scheme deadlines.

This agent places outbound calls to remind citizens about approaching deadlines
for government financial schemes they were previously found eligible for.

Run the worker with:

    uv run python src/telephony/outbound/agent.py dev

Then trigger a call from another terminal:

    uv run python src/telephony/outbound/dial.py --to <linphone-username-or-phone>

See src/telephony/README.md for trunk setup.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

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

from src.db import init_db, log_outbound_call, log_call_session
from src.telephony.outbound.prompts import (
    build_call_context_prompt,
    build_greeting,
)

logger = logging.getLogger("outbound-agent")

load_dotenv(".env.local")

OUTBOUND_TRUNK_ID = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID")
TRANSFER_TO_NUMBER = os.getenv("TRANSFER_TO_NUMBER")
CALLEE_IDENTITY = "phone-user"


# Ensure SQLite database tables are initialized
init_db()

CALL_START_TIMES = {}
CALL_LOGGED = set()
CALL_ANSWERED = set()


def record_call_outcome(
    phone_number: str,
    outcome: str,
    customer_name: str = "",
    scheme_name: str = "",
    details: str = "",
) -> dict:
    """Classify call outcome, calculate call duration, log to SQLite, and return retry rule."""
    if phone_number in CALL_LOGGED:
        return {}

    CALL_LOGGED.add(phone_number)
    start_time = CALL_START_TIMES.get(phone_number)
    duration_seconds = time.time() - start_time if start_time else 0.0

    retry_rules = {
        "NO_ANSWER": {
            "behavior": "Call not answered / Callee did not pick up.",
            "retry_recommended": True,
            "retry_in_minutes": 120,
            "max_retries": 3,
        },
        "BUSY": {
            "behavior": "Line was busy / call rejected.",
            "retry_recommended": True,
            "retry_in_minutes": 15,
            "max_retries": 3,
        },
        "VOICEMAIL": {
            "behavior": "Reached answering machine. Left brief reminder message.",
            "retry_recommended": False,
            "retry_in_minutes": 0,
            "max_retries": 0,
        },
        "EARLY_HANGUP": {
            "behavior": "Callee hung up immediately before completing greeting.",
            "retry_recommended": True,
            "retry_in_minutes": 1440,
            "max_retries": 1,
        },
        "WRONG_PERSON": {
            "behavior": "Callee confirmed they are not the intended recipient.",
            "retry_recommended": False,
            "retry_in_minutes": 0,
            "max_retries": 0,
        },
        "COMPLETED": {
            "behavior": "Call answered, identity verified, and scheme reminder delivered.",
            "retry_recommended": False,
            "retry_in_minutes": 0,
            "max_retries": 0,
        },
    }

    rule = retry_rules.get(outcome, retry_rules["NO_ANSWER"])

    # Always save call outcome and duration to SQLite database
    log_outbound_call(
        phone_number=phone_number,
        customer_name=customer_name or "Unknown",
        scheme_name=scheme_name or "Scheme",
        outcome=outcome,
        duration_seconds=duration_seconds,
        retry_recommended=rule["retry_recommended"],
    )

    sip_outcome = "success" if outcome == "COMPLETED" else "failed"
    fail_reason_map = {
        "NO_ANSWER": "No Answer / Missed Call",
        "BUSY": "Line Busy",
        "VOICEMAIL": "Answering Machine Reached",
        "EARLY_HANGUP": "Incomplete Task / Early Hangup",
        "WRONG_PERSON": "Wrong Person Reached",
        "COMPLETED": "None",
    }
    fail_reason = fail_reason_map.get(outcome, "Incomplete Task")

    log_call_session(
        session_id=f"sip_{phone_number}_{int(time.time())}",
        user_id=phone_number,
        caller_name=customer_name or "SIP Caller",
        channel="SIP",
        outcome=sip_outcome,
        failure_reason=fail_reason,
        duration_seconds=duration_seconds,
        tools_used=["outbound_scheme_reminder"],
    )

    log_msg = (
        f"\n📊 [CALL OUTCOME REPORT (SAVED TO SQLITE)]\n"
        f"  Phone/SIP:        {phone_number}\n"
        f"  Name:             {customer_name or 'Unknown'}\n"
        f"  Duration:         {duration_seconds:.1f} seconds\n"
        f"  Outcome:          {outcome}\n"
        f"  Behavior:         {rule['behavior']}\n"
        f"  Retry Required:   {rule['retry_recommended']}\n"
    )
    if rule["retry_recommended"]:
        log_msg += f"  Next Retry In:    {rule['retry_in_minutes']} minutes\n"
    if details:
        log_msg += f"  Details:          {details}\n"

    logger.info(log_msg)
    return rule


class OutboundSchemeAgent(Agent):
    def __init__(self, ctx: JobContext, metadata: dict) -> None:
        context_prompt = build_call_context_prompt(metadata)
        super().__init__(instructions=context_prompt)
        self.ctx = ctx
        self.meta = metadata

    @function_tool
    async def transfer_to_human(self, context: RunContext) -> str:
        """Transfer the person to a human colleague."""
        if not TRANSFER_TO_NUMBER:
            return "Transfers are not available on this line. Offer to have someone call back instead."

        await context.session.generate_reply(
            instructions="Tell them you're connecting them to a colleague now."
        )

        logger.info("transferring call to %s", TRANSFER_TO_NUMBER)
        try:
            await self.ctx.api.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=self.ctx.room.name,
                    participant_identity=CALLEE_IDENTITY,
                    transfer_to=f"tel:{TRANSFER_TO_NUMBER}",
                    play_dialtone=True,
                )
            )
            record_call_outcome(
                self.meta.get("phone_number", ""),
                "COMPLETED",
                "Transferred to human agent",
            )
        except Exception:
            logger.exception("transfer failed")
            return "The transfer did not go through. Apologize and offer a call back."

        return "Transferred."

    @function_tool
    async def detected_answering_machine(self, context: RunContext) -> str:
        """Handle voicemail / answering machine detection behavior and retry rule."""
        logger.info(
            "answering machine detected — leaving brief voicemail and hanging up"
        )
        record_call_outcome(
            self.meta.get("phone_number", ""),
            "VOICEMAIL",
            customer_name=self.meta.get("customer_name", ""),
            scheme_name=self.meta.get("scheme_name", ""),
        )
        asyncio.create_task(self._delayed_hangup(delay=4.0))
        return "Voicemail handled."

    @function_tool
    async def wrong_person_reached(self, context: RunContext) -> str:
        """Call this tool immediately when the caller denies identity (says 'No', 'wrong number', 'नहीं', 'मैं नहीं हूँ', etc.)."""
        logger.info("wrong person reached — apologizing and hanging up immediately")
        record_call_outcome(
            self.meta.get("phone_number", ""),
            "WRONG_PERSON",
            customer_name=self.meta.get("customer_name", ""),
            scheme_name=self.meta.get("scheme_name", ""),
            details="Callee stated wrong person / wrong number",
        )
        asyncio.create_task(self._delayed_hangup(delay=3.0))
        return "Wrong person call ended."

    @function_tool
    async def end_call(self, context: RunContext) -> str:
        """Hang up the call once finished or user opts out."""
        logger.info("ending call via end_call tool")
        record_call_outcome(
            self.meta.get("phone_number", ""),
            "COMPLETED",
            customer_name=self.meta.get("customer_name", ""),
            scheme_name=self.meta.get("scheme_name", ""),
        )
        asyncio.create_task(self._delayed_hangup(delay=3.0))
        return "Call ended."

    async def _delayed_hangup(self, delay: float = 3.0) -> None:
        """Wait for agent audio to finish playing, then delete the room to drop the SIP leg."""
        await asyncio.sleep(delay)
        try:
            logger.info("disconnecting call room %s", self.ctx.room.name)
            await self.ctx.api.room.delete_room(
                api.DeleteRoomRequest(room=self.ctx.room.name)
            )
        except Exception as e:
            logger.warning("room already closed: %s", e)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


def _parse_metadata(ctx: JobContext) -> dict:
    """Read call metadata from the dispatch job."""
    metadata = ctx.job.metadata
    if not metadata:
        return {}
    try:
        return json.loads(metadata)
    except json.JSONDecodeError:
        return {"phone_number": metadata.strip()} if metadata.strip() else {}


@server.rtc_session(agent_name="outbound-agent")
async def outbound_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    meta = _parse_metadata(ctx)
    phone_number = meta.get("phone_number")

    if not phone_number:
        logger.error("no phone number in job metadata")
        ctx.shutdown()
        return

    if not OUTBOUND_TRUNK_ID:
        logger.error("LIVEKIT_SIP_OUTBOUND_TRUNK_ID is not set — cannot place calls")
        ctx.shutdown()
        return

    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
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

    session_started = asyncio.create_task(
        session.start(
            agent=OutboundSchemeAgent(ctx, meta),
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
    )

    # Register fallback outcome logger on participant disconnect (e.g., when user hangs up manually on phone or rejects call)
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnect(participant: rtc.RemoteParticipant):
        if participant.identity == CALLEE_IDENTITY:
            cust_name = meta.get("customer_name", "Unknown")
            sch_name = meta.get("scheme_name", "Scheme")
            if phone_number in CALL_ANSWERED:
                record_call_outcome(
                    phone_number,
                    "COMPLETED",
                    customer_name=cust_name,
                    scheme_name=sch_name,
                    details="Callee completed call",
                )
            else:
                record_call_outcome(
                    phone_number,
                    "NO_ANSWER",
                    customer_name=cust_name,
                    scheme_name=sch_name,
                    details="Call not answered / missed call",
                )

    greeting = build_greeting(meta)
    logger.info("dialing %s", phone_number)
    CALL_START_TIMES[phone_number] = time.time()
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=OUTBOUND_TRUNK_ID,
                sip_call_to=phone_number,
                participant_identity=CALLEE_IDENTITY,
                participant_name="Phone user",
                wait_until_answered=True,
            )
        )
        # Call was successfully picked up / answered
        CALL_ANSWERED.add(phone_number)
    except api.TwirpError as e:
        sip_code = e.metadata.get("sip_status", "")
        cust_name = meta.get("customer_name", "Unknown")
        sch_name = meta.get("scheme_name", "Scheme")
        if "486" in sip_code or "600" in sip_code:
            record_call_outcome(
                phone_number,
                "BUSY",
                customer_name=cust_name,
                scheme_name=sch_name,
                details=f"SIP {sip_code}: Line busy",
            )
        else:
            record_call_outcome(
                phone_number,
                "NO_ANSWER",
                customer_name=cust_name,
                scheme_name=sch_name,
                details=f"SIP {sip_code}: {e.message}",
            )

        session_started.cancel()
        ctx.shutdown()
        return

    await session_started
    await session.say(greeting, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
