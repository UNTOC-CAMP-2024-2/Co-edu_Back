from fastapi import APIRouter, HTTPException, Depends,Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from user.user_db import get_userdb
from user.user_model import User,VerifiedEmail
from user.user_func import *
from user.user_schema import *
import random
import datetime

security = HTTPBearer()


router = APIRouter(
    prefix="/user",
)

@router.post("/signin")
async def signin_user(user: NewUserForm, user_db : Session = Depends(get_userdb)):
    get_duplicate(user, user_db)
    hashed_password = get_password_hash(user.password)
    db_user = User(user_id=user.user_id, password=hashed_password, name=user.name,\
                    nickname=user.nickname, email = user.email, is_mentor = user.is_mentor)
    user_db.add(db_user)
    user_db.commit()
    user_db.refresh(db_user)

    return db_user

@router.post("/login")
async def login_user(user: LoginForm, user_db : Session = Depends(get_userdb)):
    db_user = get_user(user.user_id, user_db)
    if db_user is None or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="로그인 정보 불일치.")
    
    return {"로그인여부" : "성공"}

@router.post("/email/send")
async def send_email_verification(data: EmailVerification, user_db : Session = Depends(get_userdb)):
    new_code = str(random.randint(10000,99999))
    db_email = VerifiedEmail(user_id = data.user_id, email = data.email, code = new_code,created_at = datetime.datetime.now())
    user_db.add(db_email)
    user_db.commit()
    user_db.refresh(db_email)
    email_send(data.email, new_code)
    return {"여부" : "성공적으로 인증메일이 발송되었습니다."}

@router.post("/email/verification")
async def verificate_email(data: EmailVerification, user_db : Session = Depends(get_userdb)):
    user = user_db.query(VerifiedEmail).filter(VerifiedEmail.user_id == data.user_id).first()
    if user.user_id != data.user_id or user.email != data.email or user.code != data.code:
        raise HTTPException(status_code=400, detail="일치하지 않는 정보가 있습니다.")
    user_db.delete(user)
    user_db.commit()
    return {"여부" : "인증이 완료되었습니다."}
    
@router.post("/token")
async def login(data: GetToken):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": data.user_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/getuser")
async def get_user_by_token(data: VerifyToken):
    username = token_decode(data.token)
    return {"username" : username}