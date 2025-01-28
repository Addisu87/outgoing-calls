import asyncio
import base64
import json
import os

import websockets
from calling_assistant.helpers.agent_helpers import initialize_session
from calling_assistant.prompt.agent_prompt import LOG_EVENT_TYPES
from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect

router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1",
        },
    ) as openai_ws:
        await initialize_session(openai_ws)
        stream_sid = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to OpenAI."""
            nonlocal stream_sid
            try:
                async for message in websocket.iter_bytes():
                    data = json.loads(message.decode("utf-8"))
                    if data.get("event") == "media" and openai_ws.open:
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data["media"]["payload"],
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data.get("event") == "start":
                        stream_sid = data.get("streamSid")
                        print(f"Incoming stream started: {stream_sid}")
            except WebSocketDisconnect:
                print("Client disconnected")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from OpenAI and send audio back to Twilio."""
            nonlocal stream_sid
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)

                    if response.get("type") in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}")

                    if response.get("type") == "response.audio.delta":
                        try:
                            # Simplified audio handling
                            audio_payload = base64.b64decode(response["delta"]).decode(
                                "utf-8"
                            )
                            await websocket.send_json(
                                {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {"payload": audio_payload},
                                }
                            )
                        except Exception as e:
                            print(f"Audio processing error: {e}")
                            await websocket.close(code=1011)
            except Exception as e:
                print(f"OpenAI comm error: {e}")
                await websocket.close(code=1011)

        try:
            await asyncio.gather(receive_from_twilio(), send_to_twilio())
        except Exception as e:
            print(f"Connection error: {e}")
