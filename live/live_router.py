from fastapi import WebSocket, WebSocketDisconnect,APIRouter
from typing import Dict, List
from user.user_func import *

router = APIRouter(
    prefix="/live_classroom",
)
class StudyRoomManager:
    def __init__(self):
        # Structure: {room_id: {'host': WebSocket, 'students': {user_id: WebSocket}}}
        self.rooms: Dict[str, Dict[str, Dict[str, WebSocket]]] = {}

    async def connect(self, room_id: str, role: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {"host": None, "students": {}}

        if role == "host":
            self.rooms[room_id]['host'] = websocket
        elif role == "student":
            self.rooms[room_id]['students'].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.rooms:
            if websocket == self.rooms[room_id]['host']:
                self.rooms[room_id]['host'] = None
            elif websocket in self.rooms[room_id]['students']:
                self.rooms[room_id]['students'].remove(websocket)

            # Remove the room if it is empty
            if not self.rooms[room_id]["host"] and not self.rooms[room_id]["students"]:
                del self.rooms[room_id]

    async def send_to_host(self, room_id: str, message: str):
        if room_id in self.rooms and self.rooms[room_id]['host']:
            await self.rooms[room_id]['host'].send_text(message)

manager = StudyRoomManager()

@router.websocket("/{room_id}/{role}/ws")
async def websocket_endpoint(websocket: WebSocket, room_id: str, role: str):
    await manager.connect(room_id, role, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if role == "student":
                # Only forward messages from students to the host
                await manager.send_to_host(room_id, data)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
