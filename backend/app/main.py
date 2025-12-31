from fastapi import FastAPI, WebSocket
from app.database import engine
from app import models

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Real-Time Chat App")

@app.get("/")
def read_root():
    return {"status": "Chat API is running"}

# This will eventually be your Phase 2 Real-Time Engine
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message received in room {room_id}: {data}")