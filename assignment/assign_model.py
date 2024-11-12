from sqlalchemy import Column, Integer, String,Boolean,DateTime
from classroom.cs_db import cs_Base


class AssignmentSubmission(cs_Base):
    __tablename__ = "AssignmentSubmission"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer,unique=True,nullable=False,index=True)
    user_id = Column(String(20), nullable=False, index=True)
    submitted_at = Column(DateTime) 
    code = Column(String(15), nullable=False)
    correct = Column(Boolean)


class Assignment(cs_Base):
    __tablename__ = "Assignment"
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer,unique=True,nullable=False,index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(1024), nullable=False, index=True)
    deadline = Column(DateTime)
    created_at = Column(DateTime)

class AssignmentTestCase(cs_Base):
    __tablename__ = "AssignmentTestCase"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer,unique=True,nullable=False,index=True)
    case_number = Column(Integer,nullable=False)
    input_data = Column(String(1024))
    expected_output = Column(String(1024))