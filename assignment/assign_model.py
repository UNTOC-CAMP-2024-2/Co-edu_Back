from sqlalchemy import Column, Integer, String,Boolean,DateTime
from assignment.assign_db import as_Base
from typing import List
from assign_schema import *

"""""
멘티 페이지에서의 Assignment컴포넌트의 type
전체 과제 -> done / undone
내가 제출한 과제 -> done
패드백 모아보기 -> gotFeedback

멘토 페이지에서의 Assignment컴포넌트의 type
전체 과제 -> done / undone / halfDone (멘티들이 다 했는지에 따라)
패드백 모아보기 -> gaveFeedbackAll / gaveFeedbackFew / notGaveFeedbackAll (모든 멘티에게 피드백을 주었는지에 따라)
"""""

class AssignmentSubmission(as_Base):
    __tablename__ = "AssignmentSubmission"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer,unique=True,nullable=False,index=True)
    user_id = Column(String(20), nullable=False, index=True)
    submitted_at = Column(DateTime) 
    code = Column(String(15), nullable=False)
    correct = Column(Boolean)



class Assignment(as_Base):
    __tablename__ = "Assignment"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer,unique=True,nullable=False,index=True)
    class_id = Column(Integer,unique=True,nullable=False,index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(1024), nullable=False, index=True)
    deadline = Column(DateTime)
    created_at = Column(DateTime)
    testcase = Column(List[Item])
    created_by = Column(String(20),nullable=False, index=True)

#멘티용
class AssignmentStatus(as_Base):
    __tablename__ = "AssignmnetStatus"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer,unique=True,nullable=False,index=True)
    class_id = Column(Integer,unique=True,nullable=False,index=True)
    user_id = Column(String(20), nullable=False, index=True)
    feedback = Column(String(1024), nullable=False, index=True)
    status = Column(Boolean, index=True)

