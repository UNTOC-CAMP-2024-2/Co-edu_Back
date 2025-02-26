from pydantic import BaseModel,field_validator
from fastapi import HTTPException
from typing import Optional

class ClassroomInfo(BaseModel):
    class_name : str
    class_code : str
    description : str
    max_member : int
    current_member : int
    day : str
    start_time: str
    end_time : str
    link : Optional[str]
    is_free : bool
    created_by : str
    
class NewClassroom(BaseModel):
    class_name : str
    description : str
    max_member : int
    current_member : int
    day : str
    start_time: str
    end_time : str
    link : Optional[str]
    is_access : bool
    is_free : bool

class ClassroomCode(BaseModel):
    class_code : str


class PendingApprovalInfo(BaseModel):
    user_id: str
    class_code: str
    requested_at: str

class ApprovalRequest(BaseModel):
    user_id: str
    class_code: str

class UpdateClassroomInfoRequest(BaseModel):
    class_code: str  # 수정하려는 클래스룸의 코드
    class_name: str
    description: str
    max_member: int
    day: str
    start_time: str
    end_time: str
    is_access: bool
    is_free: bool
    link: str

class KickUserForm(BaseModel):
    class_code: str
    kick_user: str