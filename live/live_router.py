from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Query,Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
import json
from assignment.restricted_execution import execute_code
from user.user_func import token_decode
from live.live_schema import Run

security = HTTPBearer()
router = APIRouter(
    prefix="/live_classroom",
)


class StudyRoomManager:
    def __init__(self):
        # key: room_id, value: {'host': WebSocket, 'students': {user_id: WebSocket}}
        self.rooms: Dict[str, Dict[str, Dict[str, WebSocket]]] = {}

    async def connect(self, room_id: str, role: str, websocket: WebSocket, user_id: Optional[str] = None):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {'host': None, 'students': {}}

        if role == "host":
            if self.rooms[room_id]['host']:
                raise HTTPException(status_code=400, detail="Host already exists for this room.")
            self.rooms[room_id]['host'] = websocket
            print(f"[INFO] Host connected to room {room_id}")
        elif role == "student":
            if not user_id:
                raise HTTPException(status_code=400, detail="Student must provide a user_id.")
            self.rooms[room_id]['students'][user_id] = websocket
            print(f"[INFO] Student {user_id} connected to room {room_id}")

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.rooms:
            if websocket == self.rooms[room_id]['host']:
                self.rooms[room_id]['host'] = None
                print(f"[INFO] Host disconnected from room {room_id}")
            else:
                for user_id, student_ws in self.rooms[room_id]['students'].items():
                    if student_ws == websocket:
                        del self.rooms[room_id]['students'][user_id]
                        print(f"[INFO] Student {user_id} disconnected from room {room_id}")
                        break

            if self.rooms[room_id]['host'] is None and not self.rooms[room_id]['students']:
                del self.rooms[room_id]
                print(f"[INFO] Room {room_id} removed (empty).")

    async def send_to_host(self, room_id: str, user_id: str, offer: Optional[dict] = None, candidate: Optional[dict] = None):
        if room_id in self.rooms and self.rooms[room_id]['host']:
            message = {"userId": user_id}
            if offer:
                message["offer"] = offer
            if candidate:
                message["candidate"] = candidate
            try:
                await self.rooms[room_id]['host'].send_text(json.dumps(message))
                print(f"[INFO] Sent data from student {user_id} to host in room {room_id}: {message}")
            except Exception as e:
                print(f"[ERROR] Failed to send data to host: {e}")

    async def send_to_student(self, room_id: str, user_id: str, answer: Optional[dict] = None, candidate: Optional[dict] = None):
        if room_id in self.rooms and user_id in self.rooms[room_id]['students']:
            message = {}
            if answer:
                message["answer"] = answer
            if candidate:
                message["candidate"] = candidate
            try:
                await self.rooms[room_id]['students'][user_id].send_text(json.dumps(message))
                print(f"[INFO] Sent data to student {user_id} in room {room_id}: {message}")
            except Exception as e:
                print(f"[ERROR] Failed to send data to student: {e}")



manager = StudyRoomManager()


@router.websocket("/{room_id}/{role}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    role: str,
    user_id: Optional[str] = Query(None)
):
    try:
        await manager.connect(room_id, role, websocket, user_id)
        while True:
            data = await websocket.receive_text()
            try:
                json_data = json.loads(data)  # JSON으로 변환
                if role == "student" and user_id:
                    # Offer 또는 Candidate를 전송
                    await manager.send_to_host(
                        room_id,
                        user_id,
                        offer=json_data.get("offer"),
                        candidate=json_data.get("candidate")
                    )
                elif role == "host":
                    # 특정 학생에게 Answer 또는 Candidate 전송
                    target_user = json_data.get("userId")
                    if target_user:
                        await manager.send_to_student(
                            room_id,
                            target_user,
                            answer=json_data.get("answer"),
                            candidate=json_data.get("candidate")
                        )
            except json.JSONDecodeError:
                print(f"[ERROR] Invalid JSON received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        print(f"[INFO] {role} {user_id or 'host'} disconnected from room {room_id}.")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


@router.post("/runcode")
async def test_assignment(data: Run,
                          credentials: HTTPAuthorizationCredentials = Security(security),
                         ):
    token = credentials.credentials
    user = token_decode(token)

    # 테스트 실행 및 결과 저장
    output, error, exec_time_s = execute_code(data.language, data.code, data.input)

    if error:
        return {
            "status": "error",
            "details" : str(error)
        }
    else:
        return {
            "status": "success",
            "details" : (output,exec_time_s)
        }