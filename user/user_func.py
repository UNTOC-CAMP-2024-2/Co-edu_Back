from sqlalchemy.orm import Session
from user_model import User
from passlib.context import CryptContext
from fastapi import APIRouter, HTTPException, Depends,Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


#사용자 정보 여부 확인
def get_user(user_id: str, db: Session):
    return db.query(User).filter(User.user_id == user_id).first()
def get_user_nickname(nickname: str, db: Session):
    return db.query(User).filter(User.nickname == nickname).first()

def get_duplicate(user, db: Session):
    if db.query(User).filter(User.user_id == user.user_id).first():
        raise HTTPException(status_code=409, detail="해당 아이디는 이미 존재합니다")
    if get_user_nickname(user.nickname, db):
        raise HTTPException(status_code=409, detail="해당 닉네임은 이미 존재합니다")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail="해당 이메일은 이미 존재합니다")
#패스워드 생성 및 확인
def get_password_hash(password):
    return pwd_context.hash(password)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)