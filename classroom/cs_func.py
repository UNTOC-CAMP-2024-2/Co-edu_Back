from sqlalchemy.orm import Session
from user.user_model import User
from passlib.context import CryptContext
from fastapi import HTTPException
from classroom.cs_model import Classroom,UserToClass
import random

def check_mentor(user_id, db: Session):
    data = db.query(User).filter(User.user_id == user_id).first()
    if data.is_mentor == True:
        return
    else:
        raise HTTPException(status_code=400, detail="멘토가 아니므로 스터디방을 생성하거나 삭제할 수 없습니다.")
    

def check_member(user_id,class_code, db: Session):
    data = db.query(UserToClass).filter(UserToClass.user_id == user_id).all()
    if class_code in data:
        raise HTTPException(status_code=409, detail="이미 가입된 스터디방입니다.")
    else:
        return
    
def check_code(code, db: Session):
    data = db.query(Classroom).filter(Classroom.class_code == code).first()
    if data:
        return None
    else:
        return code

def create_code(db: Session):
    new_code = None
    while new_code == None:
        new_code = str(random.randint(10000,99999))
        new_code = check_code(new_code,db)
    return new_code
