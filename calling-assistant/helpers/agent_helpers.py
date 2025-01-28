import json
import os
import re

from calling_assistant.prompt.agent_prompt import SYSTEM_MESSAGE
from twilio.rest import Client

# Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
PHONE_NUMBER_FROM = os.getenv("PHONE_NUMBER_FROM")
raw_domain = os.getenv("DOMAIN", "")
# Strip protocols and trailing slashes from DOMAIN
DOMAIN = re.sub(r"(^\w+:|^)\/\/|\/+$", "", raw_domain)
voice_id = os.getenv("VOICE_ID")

if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and PHONE_NUMBER_FROM):
    raise ValueError(
        "Missing Twilio environment variables. Please set them in the .env file."
    )

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


async def send_initial_conversation_item(openai_ws):
    """Send the initial conversation so AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "Greet the user with 'Hello there! I am an AI voice assistant powered by "
                        "Twilio and the OpenAI Realtime API. You can ask me for facts, jokes, or "
                        "anything you can imagine. How can I help you?'"
                    ),
                }
            ],
        },
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))


async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": voice_id,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
        },
    }

    print("Sending session update:", json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Have the AI speak first
    await send_initial_conversation_item(openai_ws)


# Phone number validation
async def check_number_allowed(to):
    """Check if a number is allowed to be called."""
    try:
        # Uncomment these line to text numbers. Only add numbers you have permission to call.
        # OVERRIDE_PHONE_NUMBERS = ["+180055551212","+15677066276"]
        # if to in OVERRIDE_PHONE_NUMBERS:
        #    return True

        incoming_numbers = client.incoming_phone_numbers.list(phone_number=to)
        if incoming_numbers:
            return True

        outgoing_caller_ids = client.outgoing_caller_ids.list(phone_number=to)
        if outgoing_caller_ids:
            return True

        return False
    except Exception as e:
        print(f"Error checking phone number: {e}")
        return False


# Create the outbound call function and a Call SID logger
async def make_call(phone_number_to_call: str):
    """Make an outbound call."""
    if not phone_number_to_call:
        raise ValueError("Please provide a phone number to call.")

    is_allowed = await check_number_allowed(phone_number_to_call)
    if not is_allowed:
        raise ValueError(
            f"The number {phone_number_to_call} is not recognized as a valid outgoing number or caller ID."
        )

    # Ensure compliance with applicable laws and regulations
    # All of the rules of TCPA apply even if a call is made by AI.
    # Do your own diligence for compliance.

    outbound_twiml = (
        f"<?xml version='1.0' encoding='UTF-8'?>"
        f"<Response><Connect><Stream url='wss://{DOMAIN}/media-stream' /></Connect></Response>"
    )

    call = client.calls.create(
        twiml=outbound_twiml,
        from_=PHONE_NUMBER_FROM,
        to=phone_number_to_call,
    )

    await log_call_sid(call.sid)


async def log_call_sid(call_sid):
    """Log the Call SID."""
    print(f"Call  started with SID: {call_sid}")
