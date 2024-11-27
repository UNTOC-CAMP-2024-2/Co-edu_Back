from pydantic import BaseModel,field_validator
from fastapi import HTTPException


class ClassroomInfo(BaseModel):
    class_name : str
    description : str
    max_member : int
    current_member : int
    day : str
    start_time: str
    end_time : str
    
class NewClassroom(ClassroomInfo):
    is_access : bool
    is_free : bool

class ClassroomCode(BaseModel):
    class_code : str

