from sqlalchemy import Column, Integer, String, Boolean
from classroom.cs_db import cs_Base

class Classroom(cs_Base):
    __tablename__ = "Classroom"
    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(255), nullable=False, index=True)
    class_code = Column(String(10),index=True, unique=True)
    description = Column(String(300))
    max_member = Column(Integer)
    current_member = Column(Integer)
    day = Column(String(15))
    start_time = Column(String(30))
    end_time = Column(String(30))
    is_access = Column(Boolean)
    is_free = Column(Boolean)
    created_by = Column(String(30),nullable = False, index=True)

class UserToClass(cs_Base):   
    __tablename__ = "UserToClass"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(20), nullable=False, index=True)
    class_code = Column(Integer,nullable=False,index=True)

class PendingApproval(cs_Base):
    __tablename__ = "PendingApproval"
    id = Column(Integer, primary_key=True, index=True) 
    user_id = Column(String(20), nullable=False, index=True)  
    class_code = Column(String(10), nullable=False, index=True)  
    requested_at = Column(String, nullable=False)