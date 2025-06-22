from sqlalchemy import Column, Integer, String,Boolean,DateTime,TEXT,JSON,ForeignKey
from assignment.assign_db import as_Base
from assignment.assign_schema import *
from sqlalchemy.orm import relationship
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
    assignment_id = Column(String(10),nullable=False,index=True)
    user_id = Column(String(20), nullable=False, index=True)
    code = Column(TEXT, nullable=False)
    correct = Column(Boolean)
    detailed_result = Column(JSON, nullable=True) 
    submitted_at = Column(String(20))
    language = Column(String(255), nullable=False)

class AssignmentCategory(as_Base):
    __tablename__ = "AssignmentCategory"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(TEXT, nullable=True)
    class_id = Column(String(10), unique=True, nullable=False, index=True)
    assignments = relationship("Assignment", back_populates="category")


class Assignment(as_Base):
    __tablename__ = "Assignment"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(String(10), unique=True, nullable=False, index=True)
    class_id = Column(String(10), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(TEXT, nullable=False, index=True)
    created_by = Column(String(20), nullable=False, index=True)

    category_id = Column(Integer, ForeignKey("AssignmentCategory.id"), nullable=True)

    category = relationship("AssignmentCategory", back_populates="assignments")

class AssignmentTestcase(as_Base):
    __tablename__ = "Testcase"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(String(10),nullable=False,index=True)
    input = Column(TEXT)
    expected_output = Column(TEXT)

class AssignmentFeedBack(as_Base):
    __tablename__ = "AssignmentFeedBack"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(String(10),nullable=False,index=True)
    user_id = Column(String(20), nullable=False, index=True)
    feedback = Column(TEXT)

