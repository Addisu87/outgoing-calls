import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.response import JSONResponse

load_dotenv()

PORT = int(os.getenv("PORT", 6060))


app = FastAPI()


@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}
