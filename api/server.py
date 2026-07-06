import json
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

# Allow React dev server to talk to this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

# Shared state - Python engine writes here, SSE streams it to the React
current_state = {
    "raw_gesture": "NONE",
    "confirmed_gesture": None,
    "hold_progress": 0.0,
    "state_machine": "IDLE"
}

def read_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)
    
def write_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

# --- RESTAPI endpoints ---
@app.get("/config")
def get_config():
    return read_config()

class GestureMapping(BaseModel):
    gesture: str
    action: str

@app.post("/config/mapping")
def update_mapping(mapping: GestureMapping):
    config = read_config()
    config["gestures"][mapping.gesture] = mapping.action
    write_config(config)
    return {"status": "ok", "updated": mapping.model_dump()}

class Settings(BaseModel):
    hold_frames: int = None
    pinch_threshold: float = None

@app.post("/config/settings")
def update_settings(settings: Settings):
    config = read_config()
    if settings.hold_frames is not None:
        config["settings"]["hold_frames"] = settings.hold_frames
    if settings.pinch_threshold is not None:
        config["settings"]["pinch_threshold"] = settings.pinch_threshold
    write_config(config)
    return {"status": "ok"}

@app.get("/state")
def get_state():
    return current_state


# --- SSE endpoint - streams live gesture state to the React frontend ---

@app.get("/stream")
async def stream_state():
    """
    Server-Sent Events endpoint.
    React connects once and receives gesture updates in real time.
    No WebSocket needed, SSE is simpler and perfect for one-directional server -> client streaming.
    """
    async def event_generator():
        last_sent = None
        while True:
            # Only send when state actually changes - no spam
            if current_state != last_sent:
                data = json.dumps(current_state)
                yield f"data: {data}\n\n"
                last_sent = current_state.copy()
            await asyncio.sleep(0.05)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )