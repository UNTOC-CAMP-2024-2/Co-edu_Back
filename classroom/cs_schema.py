from pydantic import BaseModel,field_validator
from fastapi import HTTPException

class NewClassroom(BaseModel):
    class_name : str
    description : str
    max_mameber : int