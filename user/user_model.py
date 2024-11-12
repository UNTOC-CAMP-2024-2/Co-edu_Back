from sqlalchemy import Column, Integer, String,Boolean,DateTime
from user.user_db import user_Base

class User(user_Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(20), unique=True, nullable=False, index=True)  
    password = Column(String(255), nullable=False)
    email = Column(String(40), nullable=False, index=True)
    name = Column(String(15), nullable=False)
    nickname = Column(String(15), nullable=False, unique= True, index=True)
    is_mentor = Column(Boolean)
    
class VerifiedEmail(user_Base):
    __tablename__ = "VerifiedEmails"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(20), nullable=False, index=True)
    email = Column(String(40), nullable=False, index=True)
    code = Column(String(15), nullable=False)
    created_at = Column(DateTime)

class UserToClass(user_Base):   
    __tablename__ = "UserToClass"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(20), unique=True, nullable=False, index=True)
    class_id = Column(Integer,unique=True,nullable=False,index=True)

class AssignmentSubmission(user_Base):
    __tablename__ = "AssignmentSubmission"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer,unique=True,nullable=False,index=True)
    user_id = Column(String(20), nullable=False, index=True)
    submitted_at = Column(DateTime) 
    code = Column(String(15), nullable=False)
    correct = Column(Boolean)

class Classroom(user_Base):
    __tablename__ = "Classroom"
    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(255), nullable=False, index=True)
    max_member = Column(Integer)

class Assignment(user_Base):
    __tablename__ = "Assignment"
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer,unique=True,nullable=False,index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(String(1024), nullable=False, index=True)
    deadline = Column(DateTime)
    created_at = Column(DateTime)

class AssignmentTestCase(user_Base):
    __tablename__ = "AssignmentTestCase"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer,unique=True,nullable=False,index=True)
    case_number = Column(Integer,nullable=False)
    input_data = Column(String(1024))
    expected_output = Column(String(1024))