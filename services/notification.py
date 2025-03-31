from typing import List

from starlette.websockets import WebSocket

class SocketManager:
    def __init__(self):
        self.authenticated_connections: List[WebSocket] = []
        self.public_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, is_public: bool = False):
        await websocket.accept()
        if is_public:
            self.public_connections.append(websocket)
        else:
            self.authenticated_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.authenticated_connections:
            self.authenticated_connections.remove(websocket)
        if websocket in self.public_connections:
            self.public_connections.remove(websocket)

    async def broadcast_to_authenticated(self, message):
        for connection in self.authenticated_connections:
            await connection.send_json(message)

    async def broadcast_to_public(self, message):
        for connection in self.public_connections:
            print('Send to public')
            await connection.send_json(message)

    async def broadcast_all(self, message):
        await self.broadcast_to_authenticated(message)
        await self.broadcast_to_public(message)


socket_manager = SocketManager()
