from fastapi import APIRouter, HTTPException, Depends,Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from user_db import get_userdb
from user_model import User
import os
from dotenv import load_dotenv
from user_func import *
security = HTTPBearer()


router = APIRouter(
    prefix="/user",
)

@router.post("/signin")
async def signin_user(user: User, user_db : Session = Depends(get_userdb)):
    get_duplicate(user, user_db)
    hashed_password = get_password_hash(user.password)
    db_user = User(user_id=user.user_id, password=hashed_password, name=user.name,\
                    nickname=user.nickname, email = user.email, is_mentor = user.is_mentor)
    user_db.add(db_user)
    user_db.commit()
    user_db.refresh(db_user)

    return db_user

@router.post("/login")
async def login_user(user: User, user_db : Session = Depends(get_userdb)):
    db_user = get_user(user.user_id, user_db)
    if db_user is None or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="로그인 정보 불일치.")
    
    return {"로그인여부" : "성공"}