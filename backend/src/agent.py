import logging
import asyncio
import json
import os
import db
import aiohttp
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
    inference,
    tokenize,
    room_io,
    function_tool,
    RunContext,
    get_job_context,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

import uuid
SESSION_SALT = str(uuid.uuid4())[:8]

from prompt import SYSTEM_PROMPT


class Assistant(Agent):
    def __init__(self, user_id: str) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
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
                payload = json.dumps({"type": "tool_data", "tool": tool_type, "data": data})
                await room.local_participant.publish_data(
                    payload.encode("utf-8"),
                    topic="tool-results",
                )
                logger.info(f"Successfully published tool data to frontend: {tool_type}")
            else:
                logger.warning(f"Could not publish tool data: room or local_participant not found (room={room})")
        except Exception as e:
            logger.error(f"Failed to publish tool data to frontend: {e}", exc_info=True)

    @function_tool
    async def calculate_fd_returns(self, ctx: RunContext, principal_amount: float, duration_years: float) -> str:
        """Use this tool to calculate fixed deposit (FD) returns based on the current SBI FD interest rate of 7.1 percent per annum.

        Args:
            principal_amount: The principal investment amount in Indian Rupees (INR)
            duration_years: The investment tenure in years
        """
        logger.info(f"Calculating FD returns for {principal_amount} over {duration_years} years")
        try:
            rate = 0.071  # 7.1% SBI general citizen rate
            rate_source = "SBI general citizen FD rate as of August 2026"
            n = 4  # quarterly compounding
            maturity_amount = principal_amount * ((1 + rate / n) ** (n * duration_years))
            interest_earned = maturity_amount - principal_amount
            
            p_val = int(round(principal_amount))
            t_val = round(duration_years, 1)
            i_val = int(round(interest_earned))
            m_val = int(round(maturity_amount))
            
            await self._publish_tool_data("fd_calculator", {
                "principal": p_val,
                "duration_years": t_val,
                "interest_earned": i_val,
                "maturity_amount": m_val,
                "rate": "7.1%",
                "rate_source": rate_source,
            })

            return (
                f"For a principal of {p_val} Rupees invested for {t_val} years, "
                f"the interest earned will be {i_val} Rupees, and the final maturity amount "
                f"will be {m_val} Rupees. This is based on {rate_source} at 7.1 percent per annum "
                f"with quarterly compounding."
            )
        except Exception as e:
            logger.error(f"Error calculating FD: {e}")
            return "Kripya valid numbers enter karein. Main is calculation ko nahi kar paya."

    @function_tool
    def check_scheme_eligibility(self, scheme_name: str, age: int) -> str:
        """Use this tool to check if a citizen is eligible for a specific national financial scheme based on their age.

        Args:
            scheme_name: The name of the scheme (one of: 'Jan Dhan Yojana', 'Atal Pension Yojana', 'PM Suraksha Bima Yojana', 'PM Jeevan Jyoti Bima Yojana')
            age: The age of the citizen in years
        """
        logger.info(f"Checking eligibility for {scheme_name} for age {age}")
        scheme = scheme_name.lower()
        
        if "jan dhan" in scheme or "pmjdy" in scheme:
            if age >= 10:
                return "Eligible. Citizen is eligible for Pradhan Mantri Jan Dhan Yojana. The minimum age requirement is 10 years."
            else:
                return "Not eligible. The minimum age for Pradhan Mantri Jan Dhan Yojana is 10 years."
                
        elif "atal" in scheme or "apy" in scheme or "pension" in scheme:
            if 18 <= age <= 40:
                return "Eligible. Citizen is eligible for Atal Pension Yojana. The eligible age group is 18 to 40 years."
            else:
                return "Not eligible. The eligible age group for Atal Pension Yojana is 18 to 40 years."
                
        elif "suraksha" in scheme or "pmsby" in scheme or "accident" in scheme:
            if 18 <= age <= 70:
                return "Eligible. Citizen is eligible for PM Suraksha Bima Yojana. The eligible age group is 18 to 70 years."
            else:
                return "Not eligible. The eligible age group for PM Suraksha Bima Yojana is 18 to 70 years."
                
        elif "jeevan" in scheme or "jyoti" in scheme or "pmjjby" in scheme or "life" in scheme:
            if 18 <= age <= 50:
                return "Eligible. Citizen is eligible for PM Jeevan Jyoti Bima Yojana. The eligible age group is 18 to 50 years."
            else:
                return "Not eligible. The eligible age group for PM Jeevan Jyoti Bima Yojana is 18 to 50 years."
                
        else:
            return (
                f"Unknown scheme '{scheme_name}'. "
                "Main sirf Jan Dhan Yojana, Atal Pension Yojana, PM Suraksha Bima Yojana, aur PM Jeevan Jyoti Bima Yojana ki eligibility check kar sakta hoon."
            )

    @function_tool
    async def lookup_govt_scheme(self, ctx: RunContext, scheme_name: str) -> str:
        """Use this tool when a user asks about a government financial scheme and wants to know its details such as required documents, eligibility criteria, benefits, or how to apply. This tool provides comprehensive information about Indian government schemes like Jan Dhan Yojana, Atal Pension Yojana, PM Suraksha Bima Yojana, PM Jeevan Jyoti Bima, Sukanya Samriddhi, PM Kisan, PM Mudra Yojana, and Stand-Up India.

        Args:
            scheme_name: The name or keyword of the government scheme to look up (e.g., 'Jan Dhan', 'Sukanya', 'Mudra', 'PM Kisan')
        """
        self._track_tool("lookup_govt_scheme")
        logger.info(f"lookup_govt_scheme called for: {scheme_name}")
        try:
            data_path = Path(__file__).parent / "schemes_data.json"
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            query = scheme_name.lower()
            matched = None
            for scheme in data["schemes"]:
                searchable = f"{scheme['name']} {scheme['name_hindi']} {scheme['short_name']} {scheme['id']}".lower()
                if any(word in searchable for word in query.split()):
                    matched = scheme
                    break

            if not matched:
                available = ", ".join(s["short_name"] for s in data["schemes"])
                return f"I could not find a scheme matching '{scheme_name}'. The schemes I have information about are: {available}."

            docs = ", ".join(matched["required_documents"])
            benefits = ". ".join(matched["benefits"])
            eligibility = ". ".join(matched["eligibility"]["criteria"])
            data_date = data.get("last_verified", "recently")

            await self._publish_tool_data("scheme_lookup", {
                "name": matched['name'],
                "name_hindi": matched['name_hindi'],
                "documents": matched['required_documents'],
                "benefits": matched['benefits'],
                "eligibility": matched['eligibility']['criteria'],
                "how_to_apply": matched['how_to_apply'],
                "official_url": matched['official_url'],
                "data_as_of": data_date,
            })

            return (
                f"Scheme: {matched['name']} ({matched['name_hindi']}). "
                f"Description: {matched['description']} "
                f"Eligibility: {eligibility}. "
                f"Required Documents: {docs}. "
                f"Benefits: {benefits}. "
                f"How to Apply: {matched['how_to_apply']} "
                f"Official Website: {matched['official_url']}. "
                f"This information is verified as of {data_date}."
            )
        except FileNotFoundError:
            logger.error("schemes_data.json not found")
            return "I am sorry, the scheme database is currently unavailable. Please try again later or visit myscheme.gov.in for official information."
        except Exception as e:
            logger.error(f"Error in lookup_govt_scheme: {e}")
            return "I encountered an error looking up this scheme. Please try again or visit myscheme.gov.in for official information."

    @function_tool
    async def get_gold_silver_price(self, ctx: RunContext) -> str:
        """Use this tool when a user asks about the current price of gold or silver in India. This fetches live market prices in Indian Rupees per gram."""
        self._track_tool("get_gold_silver_price")
        logger.info("get_gold_silver_price tool called")
        api_key = os.environ.get("GOLD_API_KEY", "")

        if not api_key:
            logger.warning("GOLD_API_KEY not set, using fallback prices")
            return self._gold_fallback_response("No API key configured")

        try:
            url = "https://www.goldapi.io/api/XAU/INR"
            headers = {"x-access-token": api_key, "Content-Type": "application/json"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status != 200:
                        logger.error(f"GoldAPI returned status {resp.status}")
                        return self._gold_fallback_response(f"API returned status {resp.status}")
                    gold_data = await resp.json()

            # GoldAPI returns price per troy ounce; convert to per gram
            price_per_oz = gold_data.get("price", 0)
            price_per_gram_24k = round(price_per_oz / 31.1035, 2)
            price_per_gram_22k = round(price_per_gram_24k * 0.9167, 2)
            timestamp = gold_data.get("timestamp", 0)
            data_time = datetime.fromtimestamp(timestamp).strftime("%B %d, %Y at %I:%M %p") if timestamp else "just now"

            # Now fetch silver price
            silver_price_per_gram = None
            try:
                silver_url = "https://www.goldapi.io/api/XAG/INR"
                async with aiohttp.ClientSession() as session:
                    async with session.get(silver_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            silver_data = await resp.json()
                            silver_oz = silver_data.get("price", 0)
                            silver_price_per_gram = round(silver_oz / 31.1035, 2)
            except Exception as e:
                logger.warning(f"Silver price fetch failed: {e}")

            price_data = {
                "gold_24k": int(price_per_gram_24k),
                "gold_22k": int(price_per_gram_22k),
                "silver": int(silver_price_per_gram) if silver_price_per_gram else None,
                "timestamp": data_time,
                "source": "GoldAPI.io (Live)",
            }
            await self._publish_tool_data("gold_silver_price", price_data)

            result = (
                f"Live gold price as of {data_time}: "
                f"24 karat gold is approximately {int(price_per_gram_24k)} Rupees per gram. "
                f"22 karat gold is approximately {int(price_per_gram_22k)} Rupees per gram."
            )
            if silver_price_per_gram:
                result += f" Silver is approximately {int(silver_price_per_gram)} Rupees per gram."
            result += " These are live market rates and may vary slightly at your local jeweller."
            return result

        except asyncio.TimeoutError:
            logger.error("GoldAPI request timed out")
            return self._gold_fallback_response("The price service timed out")
        except aiohttp.ClientError as e:
            logger.error(f"GoldAPI connection error: {e}")
            return self._gold_fallback_response("Could not connect to the price service")
        except Exception as e:
            logger.error(f"Error in get_gold_silver_price: {e}")
            return self._gold_fallback_response("An unexpected error occurred")

    def _gold_fallback_response(self, reason: str) -> str:
        """Returns a graceful fallback when the live gold price API is unavailable."""
        logger.info(f"Using gold price fallback. Reason: {reason}")
        return (
            f"I could not fetch live gold prices right now ({reason}). "
            f"As a rough estimate based on recent market trends in August 2026, "
            f"24 karat gold is around 7400 to 7600 Rupees per gram and "
            f"22 karat gold is around 6800 to 7000 Rupees per gram. "
            f"Silver is around 95 to 100 Rupees per gram. "
            f"For accurate current prices, please check with your local jeweller or visit goldprice.org."
        )

    @function_tool
    def lookup_caller(self) -> str:
        """Use this tool to look up details about the current caller (such as name, language preference, and historical facts) from the database."""
        logger.info(f"lookup_caller tool called for user: {self.user_id}")
        caller = db.lookup_caller(self.user_id)
        if caller:
            return json.dumps(caller)
        return "No record found for this caller."

    @function_tool
    def save_caller_info(self, name: str, language_preference: str, facts: dict, consent_given: bool) -> str:
        """Use this tool to save or update details about the current caller in the database.

        Args:
            name: The caller's name
            language_preference: The caller's language preference (e.g. 'Hindi', 'English')
            facts: A dictionary of key-value facts (e.g., schemes checked, eligibility answers). DO NOT store account or ID numbers!
            consent_given: Boolean indicating if the caller explicitly gave consent to save their details.
        """
        self._track_tool("save_caller_info")
        logger.info(f"save_caller_info tool called for user: {self.user_id}, consent: {consent_given}")
        if not consent_given:
            return "Cannot save caller information without explicit consent from the user."
        
        db.save_caller(self.user_id, name, language_preference, facts)
        return f"Successfully saved caller details for {name}."

    @function_tool
    def forget_caller(self) -> str:
        """Use this tool to delete the current caller's profile and delete all data about them from the database."""
        self._track_tool("forget_caller")
        logger.info(f"forget_caller tool called for user: {self.user_id}")
        deleted = db.delete_caller(self.user_id)
        if deleted:
            return "Successfully deleted caller profile. The caller is now forgotten."
        return "No record was found to delete."

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
        """Use this tool to create a human support escalation request when a situation requires human help (such as reported fraud/security incidents or complex disputes/policy exceptions).

        CRITICAL: You MUST get explicit consent from the user BEFORE calling this tool!

        Args:
            reason_category: The category of human help needed. One of: 'Fraud/Security Incident' or 'Complex Financial Dispute/Account Issue'
            caller_name: The name of the caller needing human help
            contact_method: The caller's preferred follow-up method (e.g. 'Phone Callback', 'SMS', 'Branch Visit', 'Email')
            issue_summary: Concise summary of what happened. DO NOT include sensitive passwords, PINs, OTPs, or bank account numbers!
            steps_already_taken: What advice or checks the agent already performed
            urgency: Urgency level of the request ('Low', 'Medium', 'High', 'Emergency')
            caller_language: Caller's preferred spoken language ('Hindi', 'English', 'Hinglish')
            consent_given: Boolean indicating if the caller explicitly gave permission to create and send this request to human support.
        """
        self._track_tool("create_escalation")
        logger.info(f"create_escalation called for user: {self.user_id}, consent: {consent_given}, reason: {reason_category}")
        if not consent_given:
            return "Escalation request cancelled. Permission was not granted by the caller."

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

        ref = rec.get("reference_id", "ESC-99999")
        status_msg = "updated existing open ticket" if rec.get("is_duplicate") else "created new ticket"

        return (
            f"Successfully {status_msg} for human support. "
            f"Reference ID: {ref}. "
            f"Priority Level: {rec.get('urgency')}. "
            f"Preferred Contact Method: {contact_method}. "
            f"Please inform the caller their Reference ID is {ref} and our human support team will follow up via {contact_method}."
        )

    @function_tool
    async def check_escalation_status(self, ctx: RunContext, reference_id: str) -> str:
        """Use this tool when a caller asks about the status of their existing human support request. They will provide a reference ID like 'ESC-12345'.

        Args:
            reference_id: The escalation reference ID (e.g. 'ESC-12345')
        """
        logger.info(f"check_escalation_status called for ref: {reference_id}")
        esc = db.lookup_escalation_by_ref(reference_id.strip().upper())
        if not esc:
            return f"No escalation ticket found with reference ID '{reference_id}'. Please verify the ID and try again."

        status = esc.get("status", "Unknown")
        category = esc.get("reason_category", "N/A")
        urgency = esc.get("urgency", "N/A")
        created = esc.get("created_at", "N/A")

        await self._publish_tool_data("escalation_status_check", {
            "reference_id": esc["reference_id"],
            "caller_name": esc["caller_name"],
            "reason_category": category,
            "urgency": urgency,
            "status": status,
            "created_at": created,
        })

        return (
            f"Escalation ticket {reference_id} status is currently: {status}. "
            f"Category: {category}. Urgency: {urgency}. "
            f"Created on: {created}. "
            f"Please inform the caller of the current status."
        )


server = AgentServer()



def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    session_start_time = datetime.now()
    session_id = f"sess_{int(session_start_time.timestamp())}_{uuid.uuid4().hex[:6]}"

    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Initialize assistant with a default user_id (will update after connecting)
    assistant = Assistant(user_id="default_user")

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        tts=murf.TTS(
            voice="Samar", 
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    def log_final_outcome():
        duration = (datetime.now() - session_start_time).total_seconds()
        tools_list = list(getattr(assistant, "tools_executed", []))
        caller_info = db.lookup_caller(assistant.user_id) if hasattr(assistant, "user_id") else None
        caller_name = caller_info.get("name") if (caller_info and isinstance(caller_info, dict)) else "Browser Caller"

        # Day 8 Objective: A call is SUCCESSFUL if the user's inquiry is resolved (i.e. at least 1 core tool executed or session > 30s)
        # Otherwise recorded as FAILED (Incomplete Task / Early Hangup).
        if len(tools_list) > 0:
            outcome = "success"
            failure_reason = "None"
        elif duration >= 30.0:
            outcome = "success"
            failure_reason = "None"
        else:
            outcome = "failed"
            failure_reason = "Incomplete Task / Early Hangup"

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
        logger.info(f"Remote participant disconnected: {participant.identity}. Logging call outcome.")
        log_final_outcome()

    try:
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

        await ctx.connect()

        user_id = "default_user"
        for _ in range(20):
            if ctx.room.remote_participants:
                user_id = list(ctx.room.remote_participants.values())[0].identity
                logger.info(f"Connected to remote participant. Found identity: {user_id}")
                break
            await asyncio.sleep(0.1)

        assistant.user_id = f"{SESSION_SALT}_{user_id}"
        assistant._room = ctx.room  # Store room ref for publishing tool data to frontend
        logger.info(f"Updated assistant user_id to: {assistant.user_id}")

        caller = db.lookup_caller(assistant.user_id)
        if caller and caller.get("name"):
            name = caller.get("name")
            lang = str(caller.get("language_preference")).lower()
            last_date = caller.get("last_interaction") or "recently"
            facts = caller.get("facts") or {}
            last_topic = facts.get("topic") or facts.get("last_topic") or "government schemes"
            
            if lang == "english":
                welcome_msg = f"Welcome back {name}! Last time on {last_date} we discussed {last_topic}. Did you apply or do you need help with anything else today?"
            else:
                welcome_msg = f"स्वागत है वापस {name} जी! पिछली बार {last_date} को हमने {last_topic} के बारे में बात की थी। क्या आपने आवेदन किया या आज मैं आपकी कोई और सहायता कर सकता हूँ?"
            
            await session.say(welcome_msg, allow_interruptions=True)
        else:
            welcome_msg = "नमस्ते! जन धन सेवा में आपका स्वागत है। Hello! Welcome to Jan Dhan Seva. How can I help you today?"
            await session.say(welcome_msg, allow_interruptions=True)
            
    finally:
        log_final_outcome()


if __name__ == "__main__":
    cli.run_app(server)
