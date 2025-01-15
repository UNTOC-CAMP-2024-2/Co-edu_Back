from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, List

router = APIRouter(
    prefix="/live_classroom",
)


class StudyRoomManager:
    def __init__(self):
        # key: room_id, value: {'host': WebSocket, 'students': List[WebSocket]}
        self.rooms: Dict[str, Dict[str, List[WebSocket]]] = {}

    async def connect(self, room_id: str, role: str, websocket: WebSocket):
        """
        Connect a client to a specific room based on its role (host or student).
        """
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {'host': None, 'students': []}

        if role == "host":
            self.rooms[room_id]['host'] = websocket
            print(f"[INFO] Host connected to room {room_id}")
        elif role == "student":
            self.rooms[room_id]['students'].append(websocket)
            print(f"[INFO] Student connected to room {room_id}")

    def disconnect(self, room_id: str, websocket: WebSocket):
        """
        Disconnect a client from the room and clean up empty rooms.
        """
        if room_id in self.rooms:
            if websocket == self.rooms[room_id]['host']:
                self.rooms[room_id]['host'] = None
                print(f"[INFO] Host disconnected from room {room_id}")
            elif websocket in self.rooms[room_id]['students']:
                self.rooms[room_id]['students'].remove(websocket)
                print(f"[INFO] Student disconnected from room {room_id}")

            # Clean up empty rooms
            if self.rooms[room_id]['host'] is None and not self.rooms[room_id]['students']:
                del self.rooms[room_id]
                print(f"[INFO] Room {room_id} removed (empty).")

    async def send_to_host(self, room_id: str, message: str):
        """
        Send a message to the host of the room.
        """
        if room_id in self.rooms and self.rooms[room_id]['host']:
            await self.rooms[room_id]['host'].send_text(message)
            try:
                await self.rooms[room_id]['host'].send_text(message)
                print(f"[INFO] Sent message to host in room {room_id}: {message}")
            except Exception as e:
                print(f"[ERROR] Failed to send message to host: {e}")

    async def broadcast_to_students(self, room_id: str, message: str):
        """
        Broadcast a message to all students in the room.
        """
        if room_id in self.rooms:
            for student in self.rooms[room_id]['students']:
                try:
                    await student.send_text(message)
                    print(f"[INFO] Sent message to a student in room {room_id}: {message}")
                except Exception as e:
                    print(f"[ERROR] Failed to send message to student: {e}")


manager = StudyRoomManager()


@router.websocket("/{room_id}/{role}/ws")
async def websocket_endpoint(websocket: WebSocket, room_id: str, role: str):
    """
    WebSocket endpoint for handling host and student connections.
    """
    await manager.connect(room_id, role, websocket)
    try:
        while True:
            # Receive a message from the WebSocket
            data = await websocket.receive_text()
            print(f"[INFO] Received message in room {room_id} from {role}: {data}")

            if role == "student":
                # Only forward messages from students to the host
                # Forward messages from students to the host
                await manager.send_to_host(room_id, data)
            elif role == "host":
                # Broadcast messages from the host to all students
                await manager.broadcast_to_students(room_id, data)
    except WebSocketDisconnect:
        # Handle client disconnection
        manager.disconnect(room_id, websocket)
        print(f"[INFO] {role} disconnected from room {room_id}.")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")