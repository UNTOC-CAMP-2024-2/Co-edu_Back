from pydantic import BaseModel
from datetime import datetime

class TestCase(BaseModel):
    input_data : str
    expected_output: str

class AssignmentData(BaseModel):
    class_id : str
    title : str
    description : str
    testcase : list[TestCase]
#deadline 삭제 

class AssignmentModify(BaseModel):
    assignment_id : str
    description : str
    title : str
    testcase : list[TestCase]

class Submit(BaseModel):
    assignment_id : str
    code : str
    language : str

class Feedback(BaseModel):
    assignment_id : str
    mentee_id : str
    feedback : str

class Test(BaseModel):
    assignment_id : str
    code : str
    language : str