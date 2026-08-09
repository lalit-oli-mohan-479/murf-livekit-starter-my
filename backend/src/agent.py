import logging
import asyncio
import json
import db

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

    @function_tool
    def calculate_fd_returns(self, principal_amount: float, duration_years: float) -> str:
        """Use this tool to calculate fixed deposit (FD) returns based on a standard 7.1 percent per annum interest rate.

        Args:
            principal_amount: The principal investment amount in Indian Rupees (INR)
            duration_years: The investment tenure in years
        """
        logger.info(f"Calculating FD returns for {principal_amount} over {duration_years} years")
        try:
            rate = 0.071 # 7.1%
            n = 4 # quarterly compounding
            maturity_amount = principal_amount * ((1 + rate / n) ** (n * duration_years))
            interest_earned = maturity_amount - principal_amount
            
            p_val = int(round(principal_amount))
            t_val = round(duration_years, 1)
            i_val = int(round(interest_earned))
            m_val = int(round(maturity_amount))
            
            return (
                f"For a principal of {p_val} Rupees invested for {t_val} years, "
                f"the interest earned will be {i_val} Rupees, and the final maturity amount "
                f"will be {m_val} Rupees at an interest rate of 7.1 percent per annum."
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
        logger.info(f"save_caller_info tool called for user: {self.user_id}, consent: {consent_given}")
        if not consent_given:
            return "Cannot save caller information without explicit consent from the user."
        
        db.save_caller(self.user_id, name, language_preference, facts)
        return f"Successfully saved caller details for {name}."

    @function_tool
    def forget_caller(self) -> str:
        """Use this tool to delete the current caller's profile and delete all data about them from the database."""
        logger.info(f"forget_caller tool called for user: {self.user_id}")
        deleted = db.delete_caller(self.user_id)
        if deleted:
            return "Successfully deleted caller profile. The caller is now forgotten."
        return "No record was found to delete."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Initialize assistant with a default user_id (will update after connecting)
    assistant = Assistant(user_id="default_user")

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Samar", 
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
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

    # Join the room and connect to the user
    await ctx.connect()

    # Find the remote participant identity (user_id) after connection
    user_id = "default_user"
    for _ in range(20):
        if ctx.room.remote_participants:
            user_id = list(ctx.room.remote_participants.values())[0].identity
            logger.info(f"Connected to remote participant. Found identity: {user_id}")
            break
        await asyncio.sleep(0.1)

    # Update assistant's user_id dynamically with Session Salt prefix
    assistant.user_id = f"{SESSION_SALT}_{user_id}"
    logger.info(f"Updated assistant user_id to: {assistant.user_id}")

    # Dynamic startup greeting based on caller's details
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
        # New caller
        welcome_msg = "नमस्ते! जन धन सेवा में आपका स्वागत है। Hello! Welcome to Jan Dhan Seva. How can I help you today?"
        await session.say(welcome_msg, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
