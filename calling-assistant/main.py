import argparse
import asyncio
import logging
import os

import uvicorn

# Import helpers and routers
from calling_assistant.helpers.agent_helpers import make_call
from calling_assistant.routers.outgoing_call import router as call_router
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

# Configure the server port
PORT = int(os.getenv("PORT", "6060"))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(call_router)


# Default route
@app.get("/", response_class=JSONResponse)
async def index_page():
        return {"message": "Twilio Media Stream Server is running!"}


# Main function to start the server or make a call
if __name__ == "__main__":
    # Argument parser to handle command-line arguments
    parser = argparse.ArgumentParser(
        description="Run the Twilio AI voice assistant server."
    )
    parser.add_argument(
        "--call",
        required=True,
        help="The phone number to call, e.g., '--call=+18005551212'",
    )
    args = parser.parse_args()

    # Run the Twilio call or start the server
    if args.call:
        phone_number = args.call
        loop = asyncio.get_event_loop()
        loop.run_until_complete(make_call(phone_number))
    else:
        uvicorn.run(app, host="0.0.0.0", port=PORT)
