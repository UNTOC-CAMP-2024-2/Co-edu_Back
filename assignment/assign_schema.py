from pydantic import BaseModel
from datetime import datetime

class TestCase(BaseModel):
    input_data : str
    expected_output: str

class AssignmentData(BaseModel):
    class_id : str
    category_id: int
    title : str
    description : str
    testcase : list[TestCase]
    time_limit: float | None = None

class AssignmentModify(BaseModel):
    assignment_id : str
    description : str
    title : str
    category_id: int 
    testcase : list[TestCase]
    time_limit: float | None = None

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

class Category(BaseModel):
    class_id: str
    name: str
    description: str | None = None

class CompletionStats(BaseModel):
    personal_completion_rate: float
    total_completion_rate: float
    total_assignments: int
    completed_assignments: int

class CategoryWithStats(BaseModel):
    id: int
    name: str
    description: str | None
    completion_stats: CompletionStats