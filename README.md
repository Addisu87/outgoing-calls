# outgoing-calls

To Make Outgoing Calls with Twilio Voice, the OpenAI Realtime API, and Python

## Prerequire

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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
