from pydantic import BaseModel
from datetime import datetime
from fastapi import HTTPException

class Item(BaseModel):
    input: str
    excepted_output: str

class AssignmentCreate(BaseModel):
    class_id : int
    title : int
    description : str
    deadline : datetime

class TestCase(BaseModel):
    assignment_id : int
    input_data : str
    expected_output: str

class GetAssign(BaseModel):
    class_id : int

class DeleteAssign(BaseModel):
    assignment_id : int

