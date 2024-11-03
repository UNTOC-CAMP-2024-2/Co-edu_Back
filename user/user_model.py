from sqlalchemy import Column, Integer, String,Boolean
from user_db import user_Base

class User(user_Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(20), unique=True, nullable=False, index=True)  
    password = Column(String(30), nullable=False)
    email = Column(String(40), nullable=False)
    name = Column(String(15), nullable=False)
    nickname = Column(String(15), nullable=False, unique= True)
    is_mentor = Column(Boolean)
    