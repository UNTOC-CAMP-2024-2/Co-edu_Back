from pydantic import BaseModel
from datetime import datetime

class AssignmentCreate(BaseModel):
    class_id : str
    title : str
    description : str
    deadline : datetime 

class TestCase(BaseModel):
    assignment_id : str
    input_data : str
    expected_output: str

class DeleteTestCase(BaseModel):
    assignment_id : str
    case_number : int

class DeleteAssign(BaseModel):
    assignment_id : str

class Submit(BaseModel):
    assignment_id : str
    code : str
    output : str

class Feedback(BaseModel):
    assignment_id : str
    mentee_id : str
    feedback : str