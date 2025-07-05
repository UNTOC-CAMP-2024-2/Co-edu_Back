from fastapi import APIRouter, HTTPException, Depends,Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from user.user_db import get_userdb
from user.user_model import User,VerifiedEmail
from user.user_func import *
from user.user_schema import *
import random
import datetime
import logging

logger = logging.getLogger("user")

security = HTTPBearer()


router = APIRouter(
    prefix="/user",
)

@router.post("/signin")
async def signin_user(user: NewUserForm, user_db : Session = Depends(get_userdb)):
    if user.user_id == None or user.password == None or user.name == None or user.email == None:
        logger.warning("[user][signin][POST][fail] params=%s, status=실패, message=필수 정보 누락", {"user_id": user.user_id, "email": user.email})
        raise HTTPException(status_code=400, detail="로그인정보의 공란을 채워주세요.")   
    get_duplicate(user, user_db)
    hashed_password = get_password_hash(user.password)
    db_user = User(user_id=user.user_id, password=hashed_password, name=user.name,\
                     email = user.email)
    user_db.add(db_user)
    user_db.commit()
    user_db.refresh(db_user)
    logger.info("[user][signin][POST][success] user_id=%s, params=%s, status=성공, message=회원가입 성공", user.user_id, {"user_id": user.user_id, "email": user.email})
    return db_user

#로그인, 토큰발급
@router.post("/login")
async def login_user(user: LoginForm, user_db : Session = Depends(get_userdb)):
    db_user = get_user(user.user_id, user_db)
    if db_user is None or not verify_password(user.password, db_user.password):
        logger.warning("[user][login][POST][fail] user_id=%s, params=%s, status=실패, message=로그인 정보 불일치", user.user_id, {"user_id": user.user_id})
        raise HTTPException(status_code=400, detail="로그인 정보 불일치.")
    else:
        access_token = create_access_token(data={"sub": user.user_id})
        refresh_token = create_refresh_token(data={"sub": user.user_id})
    user_data = user_db.query(User).filter(User.user_id == user.user_id).first()
    logger.info("[user][login][POST][success] user_id=%s, params=%s, status=성공, message=로그인 성공", user.user_id, {"user_id": user.user_id})
    return {"로그인여부" : "성공" ,"name" : user_data.name, "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

#토큰 verify
@router.post("/token/verify")
async def verify_token(data: Token):
    username = token_decode(data.token)
    logger.info("[user][token/verify][POST][success] params=%s, status=성공, message=토큰 검증 성공", {"token": data.token})
    return {"user" : username}

#토큰 만료시 : refresh_token
@router.post("/token/refresh")
async def ref_token(data: TokenRefresh):
    new_access_token = refresh_token(data.reftoken)
    logger.info("[user][token/refresh][POST][success] params=%s, status=성공, message=토큰 갱신 성공", {"reftoken": data.reftoken})
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/email/send")
async def send_email_verification(data: EmailVerification, user_db: Session = Depends(get_userdb)):
    user = get_user_email(data.email, user_db)
    if user:
        logger.warning("[user][email/send][POST][fail] params=%s, status=실패, message=이미 가입된 이메일", {"email": data.email})
        raise HTTPException(status_code=409, detail="이미 가입된 이메일주소입니다.")
    existing_email = user_db.query(VerifiedEmail).filter(VerifiedEmail.user_id == data.user_id, VerifiedEmail.email == data.email).first()

    new_code = str(random.randint(10000, 99999))
    if existing_email:
        user_db.delete(existing_email)
        user_db.commit()
    
    db_email = VerifiedEmail(
        user_id=data.user_id, 
        email=data.email, 
        code=new_code, 
        created_at=datetime.datetime.now()
    )
    user_db.add(db_email)
    user_db.commit()
    user_db.refresh(db_email)
    
    # 인증 메일 발송
    email_send(data.email, new_code)
    logger.info("[user][email/send][POST][success] user_id=%s, params=%s, status=성공, message=인증메일 발송", data.user_id, {"email": data.email})
    if existing_email:
        return {"여부": "인증메일을 재전송하였습니다."}
    else:
        return {"여부": "성공적으로 인증메일이 발송되었습니다."}

@router.post("/email/verification")
async def verificate_email(data: EmailVerification, user_db : Session = Depends(get_userdb)):
    user = user_db.query(VerifiedEmail).filter(VerifiedEmail.user_id == data.user_id, VerifiedEmail.email == data.email).first()
    if not user:
        logger.warning("[user][email/verification][POST][fail] params=%s, status=실패, message=존재하지 않는 인증정보", {"user_id": data.user_id, "email": data.email})
        raise HTTPException(status_code=404, detail="존재하지않는 정보입니다.")
    if user.user_id != data.user_id or user.email != data.email or user.code != data.code:
        logger.warning("[user][email/verification][POST][fail] params=%s, status=실패, message=일치하지 않는 인증정보", {"user_id": data.user_id, "email": data.email})
        raise HTTPException(status_code=400, detail="일치하지 않는 정보가 있습니다.")
    user_db.delete(user)
    user_db.commit()
    logger.info("[user][email/verification][POST][success] user_id=%s, params=%s, status=성공, message=이메일 인증 완료", data.user_id, {"email": data.email})
    return {"여부" : "인증이 완료되었습니다."}
