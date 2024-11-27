from sqlalchemy.orm import Session
from user.user_model import User
from passlib.context import CryptContext
from fastapi import HTTPException
from assignment.assign_model import *
import random
from typing import List

#랜덤코드 발급시 중복확인
def check_id(id, db: Session):
    data = db.query(Assignment).filter(Assignment.assignment_id == id).first()
    if data:
        return None
    else:
        return id
    