from pydantic import BaseModel,field_validator
from fastapi import HTTPException

class NewClassroom(BaseModel):
    