import argparse
import asyncio
import os

import uvicorn
from calling_assistant.helpers.agent_helpers import make_call
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse

load_dotenv()

PORT = int(os.getenv("PORT", "6060"), 10)


app = FastAPI()


@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the Twilio AI voice assistant server."
    )
    parser.add_argument(
        "--call",
        required=True,
        help="The phone number to call, e.g., '--call=+18005551212'",
    )
    args = parser.parse_args()

    phone_number = args.call

    loop = asyncio.get_event_loop()
    loop.run_until_complete(make_call(phone_number))

    uvicorn.run(app, host="0.0.0.0", port=PORT)
