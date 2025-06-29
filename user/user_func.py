from sqlalchemy.orm import Session
from user.user_model import User
from passlib.context import CryptContext
from fastapi import HTTPException,status
from variable import *
import jwt

from datetime import datetime, timedelta
from typing import Optional

from email.mime.text import MIMEText
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#토큰 생성
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#리프레시 토큰 생성
def create_refresh_token(data: dict, expires_delta: timedelta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode(token):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    return username

#토큰 유효성 검증 및 타당성 검증
def token_decode(token):
    try:
        username = decode(token)
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 잘못되었습니다.")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code= 429, detail="토큰이 만료되었습니다. 토큰을 refresh하세요.")
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 타당하지 않습니다.")

def refresh_token(token):
    try:
        username = decode(token)
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh 토큰이 잘못되었습니다.")
        new_access_token = create_access_token(data={"sub": username})
        return new_access_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Rerfresh Token이 만료되었습니다.")
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 한 Refresh Token입니다.")

#사용자 정보 여부 확인
def get_user(user_id: str, db: Session):
    return db.query(User).filter(User.user_id == user_id).first()
def get_user_email(email: str, db: Session):
    return db.query(User).filter(User.email == email).first()

def get_duplicate(user, db: Session):
    if db.query(User).filter(User.user_id == user.user_id).first():
        raise HTTPException(status_code=409, detail="해당 아이디는 이미 존재합니다")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail="해당 이메일은 이미 존재합니다")
    
#패스워드 생성 및 확인
def get_password_hash(password):
    return pwd_context.hash(password)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

#이메일전송
def email_send(email, code):
    import smtplib
    from email.mime.text import MIMEText

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                <div style="border-top: 4px solid #54CEA6; width: 100%; margin-bottom: 30px;"></div>
            <p style="color: #000; font-size: 23px; text-align: center; margin: 0; padding-bottom: 15px;">
                [ Coedu ] 메일 인증 코드
            </p>
                <p style="font-size: 16px; color: #000; text-align: center;">
                    안녕하세요. Coedu 서비스에 가입해 주셔서 감사합니다.<br>
                요청하신 <span style="color: #54CEA6; font-weight: bold;">“메일 인증 코드”</span>를 발급하였습니다.<br>
                아래의 인증 코드를 입력하여 주세요.
                </p>
                <div style="text-align: center; margin: 25px 0;">
                    <span style="font-size: 22px; font-weight: bold; color: #000; padding: 20px 30px; border: 4px solid #54CEA6; border-radius:10px; display: inline-block;">
                        {code}
                    </span> 
                </div>
                <p style="font-size: 16px; color: #000; text-align: center;">
                    감사합니다. Coedu 팀 드림
                </p>
                <div style="border-bottom: 4px solid #CED4DA; width: 100%; margin-top: 20px;"></div>
            </div>
        </body>
    </html>
    """

    msg = MIMEText(html_content, "html")
    msg['Subject'] = '[Coedu] 이메일 인증번호'

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo() 
            smtp.starttls() 
            smtp.login(EMAIL, EMAIL_PASSWORD)  

            # 이메일 전송
            smtp.sendmail(EMAIL, email, msg.as_string())

    except Exception as e:
        raise HTTPException(status_code= 400, detail="이메일전송에 실패하였습니다. 정상적인 이메일인지 확인해주세요.")

def get_user_name(user_id: str, db):
    user = db.query(User).filter(User.user_id == user_id).first()
    return user.name if user else None
