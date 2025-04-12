import asyncio
import json
import threading
from contextlib import asynccontextmanager
from datetime import datetime
import os
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.responses import StreamingResponse
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


@app.websocket("/ws-public")
async def websocket_public_endpoint(websocket: WebSocket):
    try:
        await socket_manager.connect(websocket, is_public=True)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await socket_manager.connect(websocket, is_public=False)
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
            await socket_manager.broadcast_to_authenticated(
                f"User disconnected: {len(socket_manager.authenticated_connections)} active users"
                )
    except Exception as ex:
        print(ex)


def validate_credentials(email: str, password: str) -> bool:
    return login_user(email, password)

@app.post('/close_all_positions')
async def close_all_positions(TOKEN: str, broker: str):
    if TOKEN != Config.X_TOKEN:
        return

    data = {
        'Broker': broker,
        'close-positions': True
    }
    await socket_manager.broadcast_to_public(data)

@app.post('/open_positions')
async def open_positions(TOKEN: str, symbol: str, buy: bool, broker: str):
    if TOKEN != Config.X_TOKEN:
        return

    data = {
        'Broker': broker,
        'Symbol': symbol,
        'Time': datetime.now().isoformat(),
        'Signal': "Buy" if buy else "Sell",
        'PositionOpened': datetime.now().isoformat()
    }
    await socket_manager.broadcast_to_public(data)

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

ZIP_FILE_PATH = "./project/app.zip"

def file_iterator(file_path, chunk_size=1024 * 1024):
    with open(file_path, "rb") as file:
        while chunk := file.read(chunk_size):
            yield chunk

@app.get("/download")
async def get_zip_file():
    if os.path.exists(ZIP_FILE_PATH):
        return StreamingResponse(
            file_iterator(ZIP_FILE_PATH),
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=items.zip",
                "Content-Length": str(os.path.getsize(ZIP_FILE_PATH)),
                "Accept-Ranges": "bytes",
            }
        )
    return Response(content="File not found", status_code=404)

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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


print('started')