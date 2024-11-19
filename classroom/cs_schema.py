from pydantic import BaseModel,field_validator
from fastapi import HTTPException

class NewClassroom(BaseModel):
    class_name : str
    description : str
    max_mameber : int
    day : str
    start_time : str
    end_time : str
    is_access : bool
    is_free : bool

class ClassroomCode(BaseModel):
    class_code : str

