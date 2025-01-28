# outgoing-calls

To Make Outgoing Calls with Twilio Voice, the OpenAI Realtime API, and Python

### Setup Instructions

1. Environment Setup

- set the Python version locally

```bash
pyenv local 3.11.6

```

- create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Installing Dependencies

```bash
# Core dependencies
pip install -r requirements.txt
# Development dependencies
pip install -r requirements-dev.txt

```

3. Running the Application

```bash
    uvicorn calling-assistant.main:app --reload
    uvicorn calling-assistant.main:app --host 0.0.0.0 --port $PORT
```

- The API will be live and ready to handle requests at http://127.0.0.1:6060.

## Run and test your code

### Step 1: Launch ngrok

```bash
ngrok http 6060
```

#### Step 1.1 Set the DOMAIN variable

- Copy the Forwarding address from ngrok, without the protocol (omitting the https:// in my image).

### Step 2: Run the Twilio Dev Phone

```bash
twilio dev-phone
```

### Step 3: Place an outbound call

```bash
python main.py --call=+18005551212
```
