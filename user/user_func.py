from sqlalchemy.orm import Session
from user.user_model import User
from passlib.context import CryptContext
from fastapi import HTTPException
import os
from dotenv import load_dotenv

import jwt
from datetime import datetime, timedelta
from typing import Optional

load_dotenv()

EMAIL = os.environ.get("EMAILADDRESS")
SECRET_KEY = os.environ.get("SECRET_KEY")
# token algorithm
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

from email.mime.text import MIMEText
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#토큰 생성 및 암호화/복호화
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def token_decode(token):
    decode_token = jwt.decode(jwt=token, key=SECRET_KEY,algorithms=ALGORITHM)
    return decode_token["sub"]


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

#이메일전송
def email_send(email,code):
    from main import smtp
    msg = MIMEText(f'이메일 인증코드입니다 : {code}')
    msg['Subject'] = '[Coedu] 이메일 인증번호'

    smtp.sendmail(EMAIL, email, msg.as_string())