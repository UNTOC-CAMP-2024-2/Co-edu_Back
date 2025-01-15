from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List
from user.user_func import *

router = APIRouter(
    prefix="/live_classroom",
)
security = HTTPBearer()

class StudyRoomManager:
    def __init__(self):
        # Structure: {room_id: {'host': WebSocket, 'students': {user_id: WebSocket}}}
        self.rooms: Dict[str, Dict[str, Dict[str, WebSocket]]] = {}

    async def connect(self, room_id: str, role: str, user_id: str, websocket: WebSocket):
        """
        Connects a user (host or student) to a room.
        """
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {"host": None, "students": {}}

        if role == "host":
            self.rooms[room_id]["host"] = websocket
            print(f"[INFO] Host connected to room {room_id}")
        elif role == "student":
            self.rooms[room_id]["students"][user_id] = websocket
            print(f"[INFO] Student {user_id} connected to room {room_id}")

    def disconnect(self, room_id: str, websocket: WebSocket):
        """
        Disconnects a user from the room.
        """
        if room_id in self.rooms:
            if websocket == self.rooms[room_id]["host"]:
                self.rooms[room_id]["host"] = None
                print(f"[INFO] Host disconnected from room {room_id}")
            else:
                for user_id, ws in list(self.rooms[room_id]["students"].items()):
                    if ws == websocket:
                        del self.rooms[room_id]["students"][user_id]
                        print(f"[INFO] Student {user_id} disconnected from room {room_id}")
                        break

            # Remove the room if it is empty
            if not self.rooms[room_id]["host"] and not self.rooms[room_id]["students"]:
                del self.rooms[room_id]
                print(f"[INFO] Room {room_id} removed (empty).")

    async def send_to_host(self, room_id: str, message: str):
        """
        Sends a message to the host of a room.
        """
        if room_id in self.rooms and self.rooms[room_id]["host"]:
            await self.rooms[room_id]["host"].send_text(message)

    async def send_to_student(self, room_id: str, user_id: str, message: str):
        """
        Sends a message to a specific student by user_id.
        """
        if room_id in self.rooms and user_id in self.rooms[room_id]["students"]:
            await self.rooms[room_id]["students"][user_id].send_text(message)


manager = StudyRoomManager()


@router.websocket("/{room_id}/{role}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    role: str,
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    """
    WebSocket endpoint for handling host and student connections with token-based authentication.
    """
    try:
        token = credentials.credentials
        user_id = token_decode(token)  

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token or user not authenticated")

        print(f"[INFO] User {user_id} attempting to connect to room {room_id} as {role}")


        await manager.connect(room_id, role, user_id, websocket)

        while True:
            try:
                data = await websocket.receive_text()
                print(f"[INFO] Message in room {room_id} from {role} ({user_id}): {data}")

                if role == "student":
                    await manager.send_to_host(room_id, f"Student {user_id}: {data}")
                elif role == "host":
                    for student_id, student_ws in manager.rooms[room_id]["students"].items():
                        await student_ws.send_text(f"Host: {data}")

            except WebSocketDisconnect:
                print(f"[INFO] User {user_id} disconnected from room {room_id}")
                manager.disconnect(room_id, websocket)
                break

    except HTTPException as e:
        print(f"[ERROR] Authentication failed: {e.detail}")
        await websocket.close(code=1008)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        await websocket.close(code=1011)
