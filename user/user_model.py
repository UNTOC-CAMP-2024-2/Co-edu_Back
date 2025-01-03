from sqlalchemy import Column, Integer, String,Boolean,DateTime
from user.user_db import user_Base

class User(user_Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(20), unique=True, nullable=False, index=True)  
    password = Column(String(255), nullable=False)
    email = Column(String(40), nullable=False, index=True)
    name = Column(String(15), nullable=False)
    is_mentor = Column(Boolean)
    
class VerifiedEmail(user_Base):
    __tablename__ = "VerifiedEmails"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(20), nullable=False, index=True)
    email = Column(String(40), nullable=False, index=True)
    code = Column(String(15), nullable=False)
    created_at = Column(DateTime)


