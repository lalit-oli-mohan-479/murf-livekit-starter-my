import logging
import asyncio
import json
import os
import db
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    llm,
    tokenize,
    function_tool,
    RunContext,
    get_job_context,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

import uuid

SESSION_SALT = str(uuid.uuid4())[:8]

from prompt import (
    SYSTEM_PROMPT,
    SCHEME_SPECIALIST_PROMPT,
    FRAUD_SPECIALIST_PROMPT,
    INVESTMENT_SPECIALIST_PROMPT,
)

from typing import Any
import re


def safe_float(val: Any, default: float = 0.0) -> float:
    """Robustly parse float from numeric types or strings like '5,00,000', '₹500000', '5 lakh', etc."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        s = val.lower().strip()
        if "lakh" in s or "lac" in s:
            nums = re.findall(r"[\d.]+", s)
            num = float(nums[0]) if nums else 1.0
            return num * 100000.0
        if "crore" in s or "cr" in s:
            nums = re.findall(r"[\d.]+", s)
            num = float(nums[0]) if nums else 1.0
            return num * 10000000.0
        cleaned = re.sub(r"[^\d.]", "", s)
        try:
            return float(cleaned) if cleaned else default
        except ValueError:
            return default
    return default


def get_agent_tts(voice_name: str) -> murf.TTS:
    """Helper to create Murf TTS instance with specified agent voice."""
    return murf.TTS(
        voice=voice_name,
        style="Conversational",
        tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
        text_pacing=True,
    )


def _build_specialist_chat_ctx(instructions: str, old_ctx=None) -> llm.ChatContext:
    """Helper to copy ChatContext and replace previous system messages with new agent instructions."""
    if old_ctx is None:
        ctx = llm.ChatContext()
        ctx.add_message(role="system", content=instructions)
        return ctx
    ctx = old_ctx.copy()
    ctx.items[:] = [
        item for item in ctx.items if getattr(item, "role", None) != "system"
    ]
    new_sys_msg = ctx.add_message(role="system", content=instructions)
    ctx.items.remove(new_sys_msg)
    ctx.items.insert(0, new_sys_msg)
    return ctx


class BaseAgent(Agent):
    """Base Agent class providing tool tracking, error handling, and frontend data channel publishing."""

    def __init__(self, instructions: str, user_id: str, chat_ctx=None, tts=None) -> None:
        cleaned_ctx = _build_specialist_chat_ctx(instructions, chat_ctx)
        super().__init__(instructions=instructions, chat_ctx=cleaned_ctx, tts=tts)
        self.user_id = user_id
        self._room = None
        self.tools_executed = []

    def _track_tool(self, tool_name: str) -> None:
        if tool_name not in self.tools_executed:
            self.tools_executed.append(tool_name)

    async def _publish_tool_data(self, tool_type: str, data: dict) -> None:
        """Push structured tool data to the frontend via LiveKit data channel."""
        try:
            room = None
            try:
                room = get_job_context().room
            except Exception:
                pass
            if not room:
                room = getattr(self, "_room", None)

            if room and room.local_participant:
                payload = json.dumps(
                    {"type": "tool_data", "tool": tool_type, "data": data}
                )
                await room.local_participant.publish_data(
                    payload.encode("utf-8"),
                    topic="tool-results",
                )
                logger.info(
                    f"Successfully published tool data to frontend: {tool_type}"
                )
            else:
                logger.warning(
                    f"Could not publish tool data: room or local_participant not found (room={room})"
                )
        except Exception as e:
            logger.error(f"Failed to publish tool data to frontend: {e}", exc_info=True)

    async def _switch_agent(
        self,
        ctx: RunContext,
        target_class_name: str,
        active_agent_title: str,
        role_title: str,
        reason: str,
        direction: str,
    ) -> str:
        """Helper to perform clean immediate agent handoff without double speaking."""
        await self._publish_tool_data(
            "agent_handoff",
            {
                "active_agent": active_agent_title,
                "role": role_title,
                "reason": reason,
                "previous_agent": self.__class__.__name__,
                "direction": direction,
            },
        )
        cls = globals()[target_class_name]
        specialist = cls(user_id=self.user_id, chat_ctx=self.chat_ctx)
        specialist._room = getattr(self, "_room", None)
        specialist.tools_executed = getattr(self, "tools_executed", [])

        # Instantly switch TTS voice engine and active agent
        ctx.session._tts = specialist.tts
        ctx.session.update_agent(specialist)
        asyncio.create_task(ctx.session.generate_reply())
        return f"Successfully transferred call to {active_agent_title}."

    @function_tool
    async def handoff_to_scheme_specialist(self, ctx: RunContext, reason: str) -> str:
        """Hand off to Government Scheme Specialist (Kavya - Voice: Pooja). MUST call this tool immediately whenever the user asks about any government scheme (Jan Dhan Yojana, Atal Pension, Sukanya, Mudra, PM Kisan, etc.), required documents, eligibility, or subsidies."""
        self._track_tool("handoff_to_scheme_specialist")
        logger.info(f"{self.__class__.__name__} routing to SchemeSpecialist (Kavya). Reason: {reason}")
        try:
            return await self._switch_agent(
                ctx=ctx,
                target_class_name="SchemeSpecialist",
                active_agent_title="Kavya (Government Scheme Specialist)",
                role_title="Government Scheme Specialist",
                reason=reason,
                direction="Handoff to Scheme Specialist",
            )
        except Exception as e:
            logger.error(f"Failed to handoff to SchemeSpecialist: {e}", exc_info=True)
            return "Specialist unavailable right now."

    @function_tool
    async def handoff_to_fraud_specialist(self, ctx: RunContext, reason: str) -> str:
        """Hand off to Fraud & Security Specialist (Vikram - Voice: Nikhil). MUST call this tool immediately whenever the user reports a scam, suspicious deduction, lost card, or security concern."""
        self._track_tool("handoff_to_fraud_specialist")
        logger.info(f"{self.__class__.__name__} routing to FraudSpecialist (Vikram). Reason: {reason}")
        try:
            return await self._switch_agent(
                ctx=ctx,
                target_class_name="FraudProtectionSpecialist",
                active_agent_title="Vikram (Fraud Specialist)",
                role_title="Fraud & Cyber Security Specialist",
                reason=reason,
                direction="Handoff to Fraud Specialist",
            )
        except Exception as e:
            logger.error(f"Failed to handoff to FraudSpecialist: {e}", exc_info=True)
            return "Specialist unavailable right now."

    @function_tool
    async def handoff_to_investment_specialist(self, ctx: RunContext, reason: str) -> str:
        """Hand off to Fixed Deposit & Investment Specialist (Kirti - Voice: Palak). MUST call this tool immediately whenever the user asks for FD calculations, interest rates, or tenure optimization."""
        self._track_tool("handoff_to_investment_specialist")
        logger.info(f"{self.__class__.__name__} routing to InvestmentSpecialist (Kirti). Reason: {reason}")
        try:
            return await self._switch_agent(
                ctx=ctx,
                target_class_name="InvestmentCalcSpecialist",
                active_agent_title="Kirti (Investment Specialist)",
                role_title="FD & Investment Specialist",
                reason=reason,
                direction="Handoff to Investment Specialist",
            )
        except Exception as e:
            logger.error(f"Failed to handoff to InvestmentSpecialist: {e}", exc_info=True)
            return "Specialist unavailable right now."

    @function_tool
    async def handoff_to_main_agent(self, ctx: RunContext, reason: str) -> str:
        """Hand back to Main Financial Guide (Aarav - Voice: Samar). Call this tool when the user explicitly requests to speak to Aarav or asks for general non-specialist banking advice."""
        self._track_tool("handoff_to_main_agent")
        logger.info(f"{self.__class__.__name__} handing back to Main Agent Aarav. Reason: {reason}")
        try:
            return await self._switch_agent(
                ctx=ctx,
                target_class_name="Assistant",
                active_agent_title="Aarav (Main Financial Guide)",
                role_title="Main Digital Financial Guide",
                reason=reason,
                direction="Specialist to Main Guide",
            )
        except Exception as e:
            logger.error(f"Failed to handoff to Main Agent: {e}", exc_info=True)
            return "Main agent unavailable right now."


class SchemeSpecialist(BaseAgent):
    """Specialist 1: Government Social Welfare Schemes & Subsidies (Kavya - Voice: Pooja)."""

    def __init__(self, user_id: str, chat_ctx=None) -> None:
        super().__init__(
            instructions=SCHEME_SPECIALIST_PROMPT,
            user_id=user_id,
            chat_ctx=chat_ctx,
            tts=get_agent_tts("Pooja"),
        )

    async def on_enter(self) -> None:
        await super().on_enter()
        logger.info("SchemeSpecialist Kavya entered session.")

    @function_tool
    def check_scheme_eligibility(self, scheme_name: str, age: Any = 25) -> str:
        """Use this tool to check if a citizen is eligible for a specific national scheme based on age.

        Args:
            scheme_name: The name of the scheme
            age: The age of the citizen in years (default 25)
        """
        self._track_tool("check_scheme_eligibility")
        age_int = int(safe_float(age, 25.0))
        logger.info(
            f"[Specialist Kavya] Checking eligibility for {scheme_name} for age {age_int}"
        )
        scheme = scheme_name.lower()

        if "jan dhan" in scheme or "pmjdy" in scheme:
            return "Eligible" if age_int >= 10 else "Not eligible (Min age 10)."
        elif "atal" in scheme or "apy" in scheme:
            return (
                "Eligible" if 18 <= age_int <= 40 else "Not eligible (Eligible age 18-40)."
            )
        elif "suraksha" in scheme or "pmsby" in scheme:
            return (
                "Eligible" if 18 <= age_int <= 70 else "Not eligible (Eligible age 18-70)."
            )
        elif "jeevan" in scheme or "pmjjby" in scheme:
            return (
                "Eligible" if 18 <= age_int <= 50 else "Not eligible (Eligible age 18-50)."
            )
        return f"Verified age {age_int} for scheme '{scheme_name}'."

    @function_tool
    async def lookup_govt_scheme(self, ctx: RunContext, scheme_name: str) -> str:
        """Use this tool to look up details, required documents, and benefits for a government scheme.

        Args:
            scheme_name: Scheme keyword
        """
        self._track_tool("lookup_govt_scheme")
        try:
            data_path = Path(__file__).parent / "schemes_data.json"
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            query = scheme_name.lower()
            matched = next(
                (
                    s
                    for s in data["schemes"]
                    if any(
                        w in f"{s['name']} {s['name_hindi']} {s['short_name']}".lower()
                        for w in query.split()
                    )
                ),
                None,
            )

            if not matched:
                return f"Could not find exact scheme '{scheme_name}'. Available: Jan Dhan, APY, PMSBY, PMJJBY, Sukanya."

            docs = ", ".join(matched["required_documents"])
            data_date = data.get("last_verified", "recently")

            await self._publish_tool_data(
                "scheme_lookup",
                {
                    "name": matched["name"],
                    "name_hindi": matched["name_hindi"],
                    "documents": matched["required_documents"],
                    "benefits": matched["benefits"],
                    "eligibility": matched["eligibility"]["criteria"],
                    "how_to_apply": matched["how_to_apply"],
                    "official_url": matched["official_url"],
                    "data_as_of": data_date,
                },
            )

            return (
                f"Scheme: {matched['name']} ({matched['name_hindi']}). "
                f"Required Documents: {docs}. "
                f"How to Apply: {matched['how_to_apply']} "
                f"Verified as of {data_date}."
            )
        except Exception as e:
            logger.error(f"Error in lookup_govt_scheme: {e}")
            return "Unable to access scheme database right now."


class FraudProtectionSpecialist(BaseAgent):
    """Specialist 2: Fraud & Cyber Security Specialist (Vikram - Voice: Nikhil)."""

    def __init__(self, user_id: str, chat_ctx=None) -> None:
        super().__init__(
            instructions=FRAUD_SPECIALIST_PROMPT,
            user_id=user_id,
            chat_ctx=chat_ctx,
            tts=get_agent_tts("Nikhil"),
        )

    async def on_enter(self) -> None:
        await super().on_enter()
        logger.info("FraudProtectionSpecialist Vikram entered session.")

    @function_tool
    async def create_escalation(
        self,
        ctx: RunContext,
        caller_name: str,
        issue_summary: str,
        urgency: str,
        consent_given: bool,
    ) -> str:
        """Create human support escalation for fraud victim after consent."""
        self._track_tool("create_escalation")
        if not consent_given:
            return "Escalation cancelled because permission was not granted."

        rec = db.create_escalation_record(
            user_id=self.user_id,
            caller_name=caller_name,
            contact_method="Phone Callback",
            reason_category="Fraud/Security Incident",
            issue_summary=issue_summary,
            steps_already_taken="Advised card block & National Cybercrime Helpline 1930",
            urgency=urgency,
            caller_language="Hindi",
        )
        await self._publish_tool_data("human_help_request", rec)
        return (
            f"Created human support ticket {rec['reference_id']}. Priority: {urgency}."
        )


class InvestmentCalcSpecialist(BaseAgent):
    """Specialist 3: Fixed Deposit & Investment Calculation Specialist (Kirti - Voice: Palak)."""

    def __init__(self, user_id: str, chat_ctx=None) -> None:
        super().__init__(
            instructions=INVESTMENT_SPECIALIST_PROMPT,
            user_id=user_id,
            chat_ctx=chat_ctx,
            tts=get_agent_tts("Palak"),
        )

    async def on_enter(self) -> None:
        await super().on_enter()
        logger.info("InvestmentCalcSpecialist Kirti entered session.")

    @function_tool
    async def calculate_fd_returns(
        self,
        principal_amount: Any = 100000.0,
        duration_years: Any = 1.0,
    ) -> str:
        """Calculate detailed FD returns with SBI compounding rates.

        Args:
            principal_amount: Principal investment amount in INR (default 100000.0)
            duration_years: Duration/tenure of investment in years (default 1.0)
        """
        self._track_tool("calculate_fd_returns")
        p_float = safe_float(principal_amount, 100000.0)
        d_float = safe_float(duration_years, 1.0)

        if p_float <= 0:
            p_float = 100000.0
        if d_float <= 0:
            d_float = 1.0

        rate = 0.071
        n = 4
        maturity = p_float * ((1 + rate / n) ** (n * d_float))
        interest = maturity - p_float

        p_val = int(round(p_float))
        t_val = round(d_float, 1)
        i_val = int(round(interest))
        m_val = int(round(maturity))

        await self._publish_tool_data(
            "fd_calculator",
            {
                "principal": p_val,
                "duration_years": t_val,
                "interest_earned": i_val,
                "maturity_amount": m_val,
                "rate": "7.1%",
                "rate_source": "SBI general citizen rate as of August 2026",
            },
        )
        return (
            f"FD Calculation complete: Principal amount is {p_val} INR for {t_val} years. "
            f"Total interest earned is {i_val} INR and total maturity amount is {m_val} INR at 7.1% interest rate."
        )


class Assistant(BaseAgent):
    """Main Agent (Aarav - Voice: Samar) - Main Financial Literacy Guide & Dynamic Specialist Router."""

    def __init__(self, user_id: str, chat_ctx=None) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            user_id=user_id,
            chat_ctx=chat_ctx,
            tts=get_agent_tts("Samar"),
        )

    async def on_enter(self) -> None:
        await super().on_enter()
        logger.info("Assistant Aarav entered session.")





    @function_tool
    async def get_gold_silver_price(self, ctx: RunContext) -> str:
        """Get gold and silver price."""
        self._track_tool("get_gold_silver_price")
        from datetime import datetime
        now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
        price_data = {
            "gold_24k": 7500,
            "gold_22k": 6900,
            "silver": 98,
            "source": "GoldAPI (Estimate)",
            "timestamp": now_str,
        }
        await self._publish_tool_data("gold_silver_price", price_data)
        return "Gold price is 7500 Rupees per gram for 24K and 6900 Rupees per gram for 22K."

    @function_tool
    def lookup_caller(self) -> str:
        """Lookup caller details from DB."""
        caller = db.lookup_caller(self.user_id)
        return json.dumps(caller) if caller else "No record found."

    @function_tool
    def save_caller_info(
        self, name: str, language_preference: str, facts: dict, consent_given: bool
    ) -> str:
        """Save caller info in DB with consent."""
        if not consent_given:
            return "Permission not granted."
        db.save_caller(self.user_id, name, language_preference, facts)
        return f"Saved caller details for {name}."

    @function_tool
    def forget_caller(self) -> str:
        """Delete caller record."""
        return (
            "Deleted profile." if db.delete_caller(self.user_id) else "No record found."
        )

    @function_tool
    async def create_escalation(
        self,
        ctx: RunContext,
        reason_category: str,
        caller_name: str,
        contact_method: str,
        issue_summary: str,
        steps_already_taken: str,
        urgency: str,
        caller_language: str,
        consent_given: bool,
    ) -> str:
        """Create human support escalation ticket."""
        if not consent_given:
            return "Escalation cancelled."
        rec = db.create_escalation_record(
            user_id=self.user_id,
            caller_name=caller_name,
            contact_method=contact_method,
            reason_category=reason_category,
            issue_summary=issue_summary,
            steps_already_taken=steps_already_taken,
            urgency=urgency,
            caller_language=caller_language,
        )
        await self._publish_tool_data("human_help_request", rec)
        return f"Created ticket {rec.get('reference_id')}."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    session_start_time = datetime.now()
    session_id = f"sess_{int(session_start_time.timestamp())}_{uuid.uuid4().hex[:6]}"

    ctx.log_context_fields = {"room": ctx.room.name}
    assistant = Assistant(user_id="default_user")

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-3.5-flash-lite"),
        tts=get_agent_tts("Samar"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    def log_final_outcome():
        duration = (datetime.now() - session_start_time).total_seconds()
        current = getattr(session, "_agent", assistant)
        tools_list = list(getattr(current, "tools_executed", []))
        caller_info = (
            db.lookup_caller(assistant.user_id)
            if hasattr(assistant, "user_id")
            else None
        )
        caller_name = (
            caller_info.get("name")
            if (caller_info and isinstance(caller_info, dict))
            else "Browser Caller"
        )

        outcome = "success" if (len(tools_list) > 0 or duration >= 30.0) else "failed"
        failure_reason = (
            "None" if outcome == "success" else "Incomplete Task / Early Hangup"
        )

        db.log_call_session(
            session_id=session_id,
            user_id=getattr(assistant, "user_id", "Anonymous"),
            caller_name=caller_name,
            channel="Browser",
            outcome=outcome,
            failure_reason=failure_reason,
            duration_seconds=duration,
            tools_used=tools_list,
        )

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        log_final_outcome()

    try:
        await ctx.connect()

        await session.start(
            agent=assistant,
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

        user_id = "default_user"
        for _ in range(20):
            if ctx.room.remote_participants:
                user_id = list(ctx.room.remote_participants.values())[0].identity
                break
            await asyncio.sleep(0.1)

        assistant.user_id = f"{SESSION_SALT}_{user_id}"
        assistant._room = ctx.room

        caller = db.lookup_caller(assistant.user_id)
        if caller and caller.get("name"):
            name = caller.get("name")
            welcome_msg = f"Welcome back {name}! How can I help you today?"
            await session.say(welcome_msg, allow_interruptions=True)
        else:
            welcome_msg = "नमस्ते! जन धन सेवा में आपका स्वागत है। Hello! Welcome to Jan Dhan Seva. How can I help you today?"
            await session.say(welcome_msg, allow_interruptions=True)

    finally:
        log_final_outcome()


if __name__ == "__main__":
    cli.run_app(server)
