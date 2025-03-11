import threading
from contextlib import asynccontextmanager
from datetime import datetime
import os
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket, WebSocketDisconnect

from config import Config
from services.firebase import login_user, db
from services.notification import socket_manager
from services.trading_view import TradingView
from firebase_admin import firestore

@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = threading.Event()
    def run_bot():
        bot = TradingView(
            Config.captcha_api,
            Config.username,
            Config.password,
            stop_event,
            Config.chart_link,
            socket_manager
        )
        bot.login()
        bot.openChart()
        while not stop_event.is_set():
            pass

    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    yield

    stop_event.set()
    bot_thread.join()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await socket_manager.connect(websocket)
    data = await websocket.receive_text()
    try:
        params = dict(pair.split('=') for pair in data.split('&'))
        email = params.get('email')
        password = params.get('password')

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required.")

        if not validate_credentials(email, password):
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        socket_manager.disconnect(websocket)
        await socket_manager.broadcast(
            f"User disconnected: {len(socket_manager.active_connections)} active users"
            )


def validate_credentials(email: str, password: str) -> bool:
    return login_user(email, password)

@app.post('/auth')
async def sign_in(username: str, password: str):
    return login_user(username, password)

@app.post('/subscription')
async def subscription(subscription_type: str, end_at: str, subscription_id: str, email: str):
    subscription_data = {
        "subscription_type": subscription_type,
        "end_At": end_at,
        "subscription_id": subscription_id,
        "timestamp": firestore.SERVER_TIMESTAMP
    }

    try:
        db.collection("subscriptions").document(email).set(subscription_data, merge=True)
    except Exception as e:
        print(f"{e}")

ZIP_FILE_PATH = "./project/app.zip"

@app.get("/download")
async def get_zip_file():
    if os.path.exists(ZIP_FILE_PATH):
        return FileResponse(ZIP_FILE_PATH, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=items.zip"})
    return {"error": "File not found"}

@app.get('/get_subscription/{user_id}')
async def get_subscription(user_id: str):
    try:
        doc_ref = db.collection("subscriptions").document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            return {"status": "success", "data": doc.to_dict()}
        else:
            raise HTTPException(status_code=404, detail="Subscription not found for this user")

    except Exception as e:
        print(f"Error fetching subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")