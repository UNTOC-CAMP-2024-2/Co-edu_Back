from sqlalchemy import Column, Integer, String
from classroom.cs_db import cs_Base


class Classroom(cs_Base):
    __tablename__ = "Classroom"
    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(255), nullable=False, index=True)
    class_code = Column(String(10),index=True, unique=True)
    description = Column(String(300))
    max_member = Column(Integer)
    created_by = Column(String(30),nullable = False, index=True)

class UserToClass(cs_Base):   
    __tablename__ = "UserToClass"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(20), unique=True, nullable=False, index=True)
    class_code = Column(Integer,unique=True,nullable=False,index=True)