"""Server-only Agora AgentKit integration.
Never move Agora credentials to React.
"""

import asyncio
import os
import secrets
import time

from dotenv import load_dotenv

load_dotenv()


# Public MCP server used by the Agora agent.
MCP_SERVER_URL = (
    "https://germproof-viscous-unlearned.ngrok-free.dev/mcp/"
)


PROMPT = """
You are Calling Buddy, an AI public-assistance voice agent, not a human.

Start with:
"Hello! Welcome to Calling Buddy. Which language would you like to speak?"

Continue in the user's chosen language.

Support:
- English
- Hindi
- Hindi-English code switching (Hinglish)

Keep responses short, natural, and conversational.

LIVE INFORMATION:
You have access to a tool called search_web.

SYSTEM CONTROL:

You also have access to a tool called open_application.

Use open_application whenever the user asks you to open a
Windows application on their computer.

Examples:
- "Open Task Manager" → open_application("Task Manager")
- "Open VS Code" → open_application("VS Code")
- "Open Chrome" → open_application("Chrome")
- "Open Calculator" → open_application("Calculator")
- "Open File Explorer" → open_application("File Explorer")

Do not use search_web for application-opening requests.

When the tool successfully opens an application, briefly tell
the user that it has been opened.

Use search_web whenever the user asks for information that may
change over time, including:
- Current currency exchange rates
- Current prices
- Current news
- Current weather
- Current public information
- Current electricity/outage information
- Other real-time information

Do NOT pretend to know current information from memory.

For example:
User: "What is the current USD to INR rate?"
→ Use search_web.
→ Give the user the result briefly.

If search_web cannot verify the information, clearly tell the user
that you could not verify it.

For electricity-related issues:
- Collect the user's city and PIN code when needed.
- Use search_web to look for current information when appropriate.
- Never invent outage information.
- If outage information cannot be verified, clearly say so.
- Escalate when uncertain.

For normal conversation:
- Do not call search_web unnecessarily.
- Answer naturally and briefly.

Safety:
- Do not diagnose medical conditions.
- Do not replace emergency responders.
- Do not give authoritative legal advice.
- Do not give authoritative financial advice.
"""


class AgoraService:

    def __init__(self):
        self.sessions = {}

    def status(self):
        app_id = os.getenv("AGORA_APP_ID")
        certificate = os.getenv("AGORA_APP_CERTIFICATE")

        if app_id and certificate:
            return "ready"

        return "configuration_required"

    async def start_session(self):

        app_id = os.getenv("AGORA_APP_ID")
        certificate = os.getenv("AGORA_APP_CERTIFICATE")

        if not app_id or not certificate:
            raise RuntimeError(
                "Agora credentials are not configured on the server."
            )

        try:
            from agora_agent import (
                Agent,
                Agora,
                Area,
                DeepgramSTT,
                MiniMaxTTS,
                OpenAI,
                expires_in_hours,
            )

            from agora_token_builder import RtcTokenBuilder

        except ImportError as exc:
            raise RuntimeError(
                "Required Agora packages are not installed. "
                "Install agora-agents and agora-token-builder."
            ) from exc

        # Create unique IDs for this voice session.
        session_id = secrets.token_urlsafe(16)
        channel = f"echosphere-{session_id[:16]}"

        user_uid = secrets.randbelow(1_000_000_000) + 1
        agent_uid = secrets.randbelow(1_000_000_000) + 1

        try:
            # Agora Conversational AI client.
            client = Agora(
                area=Area.US,
                app_id=app_id,
                app_certificate=certificate,
            )

            # Build the Calling Buddy voice agent.
            agent = (
                Agent(
                    client=client,
                    turn_detection={
                        "language": "en-US"
                    },
                )
                .with_stt(
                    DeepgramSTT(
                        model="nova-3",
                        language="en",
                        smart_format=True,
                        punctuation=True,
                    )
                )
                .with_llm(
                    OpenAI(
                        model="gpt-4o-mini",
                        system_messages=[
                            {
                                "role": "system",
                                "content": PROMPT,
                            }
                        ],
                        greeting_message=(
                            "Hello! Welcome to Calling Buddy. "
                            "Which language would you like to speak?"
                        ),
                        max_history=30,

                        # Connect Agora's LLM to our MCP server.
    mcp_servers=[
    {
        "name": "echosphere-web-search",
        "endpoint": MCP_SERVER_URL
    }
],
                    )
                )
                .with_tools(True)
                .with_tts(
                    MiniMaxTTS(
                        model="speech_2_6_turbo",
                        voice_id="English_captivating_female1",
                    )
                )
            )

            # Create an Agora Conversational AI session.
            agent_session = agent.create_session(
                channel=channel,
                agent_uid=str(agent_uid),
                remote_uids=["*"],
                name=f"calling-buddy-{int(time.time())}",
                idle_timeout=120,
                expires_in=expires_in_hours(1),
            )

            # Start the Conversational AI agent.
            agent_id = await asyncio.to_thread(
                agent_session.start
            )

            # Generate a short-lived RTC token for the browser user.
            token_expiry = int(time.time()) + 3600

            rtc_token = RtcTokenBuilder.buildTokenWithUid(
                app_id,
                certificate,
                channel,
                user_uid,
                1,
                token_expiry,
            )

        except Exception as exc:
            print(
                f"Agora Calling Buddy session failed: "
                f"{type(exc).__name__}: {exc}"
            )

            raise RuntimeError(
                "Agora could not start the Calling Buddy voice session. "
                "Check Agora project configuration and Conversational AI access."
            ) from exc

        # Keep the active session on the backend.
        self.sessions[session_id] = agent_session

        return {
            "session_id": session_id,
            "app_id": app_id,
            "channel": channel,
            "user_uid": user_uid,
            "rtc_token": rtc_token,
            "agent_id": agent_id,
        }

    async def stop_session(self, session_id):

        session = self.sessions.pop(
            session_id,
            None,
        )

        if session is None:
            return {
                "session_id": session_id,
                "status": "already_stopped",
            }

        try:
            await asyncio.to_thread(
                session.stop
            )

        except Exception as exc:
            print(
                f"Failed to stop Agora session: "
                f"{type(exc).__name__}: {exc}"
            )

            raise RuntimeError(
                "Agora could not stop the voice session."
            ) from exc

        return {
            "session_id": session_id,
            "status": "stopped",
        }