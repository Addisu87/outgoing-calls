import os
import json
import base64
import asyncio
import websockets

from fastapi import APIRouter, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketDisconnect

from calling-assistant.prompt.agent_prompt import LOG_EVENT_TYPES
from calling_assistant.helpers.agent_helpers import initialize_session

router = APIRouter()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()
    

    async with websockets.connect(
        "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
            await initialize_session(openai_ws())
            stream_sid = None
            
            async def receive_from_twilio():
                """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
                nonlocal stream_sid
                try:
                    async for message in websocket.iter_text():
                        data = json.loads(message)
                        if data["event"] == "media" and openai_ws.open:
                            audio_append = {
                                "type": "input_audio_buffer.append",
                                "audio": data["media"]["payload"]
                            }
                            await openai_ws.send(json.dumps(audio_append))
                        elif data["event"] == "start":
                            stream_sid = data["stream_sid"]["streamSid"]
                            print(f"Incoming stream has started {stream_sid}")
                except WebSocketDisconnect:
                    print("Client disconnected")
                    if openai_ws.open:
                        await openai_ws.close()
                        
            async def send_to_twilio():
                """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
                nonlocal stream_sid
                try: 
                    async for openai_message in openai_ws:
                        response = json.loads(openai_message)
                        
                        if response["type"] in LOG_EVENT_TYPES:
                            print(f"Received event: {response['type']}", response)
                        if response["type"] == "session.updated":
                            print("Session updated successfully:", response)
                            
                        if response["type"] =="response.audio.delta" and response.get("delta"):
                            try:
                                audio_payload = base64.b64encode(base64.b64decode(response["delta"])).decode("utf-8")
                                audio_delta = {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": audio_payload,
                                    }
                                }
                                await websocket.send_json(audio_delta)
                            except Exception as e:
                                print(f"Error sending audio to Twilio: {e}")
                                raise HTTPException(status_code=500, detail=str(e))
                            
                except Exception as e:
                    print(f"Error in send_to_twilio: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            await asyncio.gather(receive_from_twilio(), send_to_twilio())
                                
