from sqlalchemy.orm import Session
from user.user_model import User
from passlib.context import CryptContext
from fastapi import HTTPException

def check_mentor(user_id, db: Session):
    data = db.query(User).filter(User.user_id == user_id).first()
    if data.is_mentor == True:
        return
    else:
        raise HTTPException(status_code=400, detail="멘토가 아니므로 스터디방을 생성하실 수 없습니다.")