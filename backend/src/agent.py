import logging

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
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

SYSTEM_PROMPT = """You are a helpful, patient, and knowledgeable voice assistant specializing in Indian financial literacy and banking. Your primary goals are:
1. Explain Government schemes (such as Jan Dhan Yojana, Atal Pension Yojana, Sukanya Samriddhi Yojana, Jeevan Jyoti Bima Yojana, and Suraksha Bima Yojana) in simple, easy-to-understand terms.
2. Teach basic banking literacy, such as how savings accounts, fixed deposits, UPI, and interest work.
3. Spread fraud awareness by reminding users to never share their OTPs, UPI PINs, or bank passwords, and warning them about common phone scams and phishing links.

Keep your tone conversational, warm, and friendly. Since this is a voice conversation:
- Keep your answers concise, ideally two to three sentences at a time.
- Avoid all markdown formatting, bullet points, asterisks, emojis, symbols, or lists. Write in pure plain text.
- If explaining a complex scheme, break it down and ask the user if they would like to hear more details."""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."

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


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Nikhil", 
                locale="en-IN",
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
        agent=Assistant(),
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


if __name__ == "__main__":
    cli.run_app(server)
