from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.core.db import engine, Base
from app.api.routes import router
import asyncio
import redis
import threading

app = FastAPI()

connections = []
r = redis.Redis(host="localhost", port=6379, db=0)

# ✅ WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except:
        connections.remove(websocket)

# ✅ Redis listener (FIXED)
def redis_listener():
    pubsub = r.pubsub()
    pubsub.subscribe("job_updates")

    for message in pubsub.listen():
        if message["type"] == "message":
            data = message["data"].decode()

            for ws in connections:
                try:
                    asyncio.run(ws.send_text(data))
                except:
                    pass

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=redis_listener, daemon=True)
    thread.start()

Base.metadata.create_all(bind=engine)
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Backend Running"}