from fastapi import WebSocket, WebSocketDisconnect,APIRouter
from typing import Dict, List

router = APIRouter(
    prefix="/live_classroom",
)
# 클라이언트 연결을 관리하기 위한 데이터 구조
class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Dict[str, List[WebSocket]]] = {}

    async def connect(self, room_id: str, role: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {"host": None, "students": []}
        if role == "host":
            self.rooms[room_id]["host"] = websocket
        else:
            self.rooms[room_id]["students"].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.rooms:
            if self.rooms[room_id]["host"] == websocket:
                self.rooms[room_id]["host"] = None
            elif websocket in self.rooms[room_id]["students"]:
                self.rooms[room_id]["students"].remove(websocket)

    async def send_to_host(self, room_id: str, message: dict):
        host = self.rooms.get(room_id, {}).get("host")
        if host:
            await host.send_json(message)

    async def send_to_student(self, room_id: str, student_index: int, message: dict):
        students = self.rooms.get(room_id, {}).get("students", [])
        if len(students) > student_index:
            await students[student_index].send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/{room_id}/{role}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, role: str):
    # 클라이언트 연결 처리
    await manager.connect(room_id, role, websocket)
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "offer" or message_type == "candidate":
                # 학생이 offer 또는 candidate를 보낼 경우, 호스트에게 전달
                await manager.send_to_host(room_id, data)
            elif message_type == "answer":
                # 호스트가 answer를 보낼 경우, 해당 학생에게 전달
                target_index = data.get("target_index", 0)
                await manager.send_to_student(room_id, target_index, data)
    except WebSocketDisconnect:
        # 클라이언트가 연결을 끊었을 때
        manager.disconnect(room_id, websocket)
