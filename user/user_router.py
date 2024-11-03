from fastapi import APIRouter, HTTPException, Depends,Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from user_db import get_userdb
from user_model import User
import os
from dotenv import load_dotenv
from user_func import get_user,get_user_nickname,get_password_hash
security = HTTPBearer()


router = APIRouter(
    prefix="/user",
)

@router.post("/signin")
async def signin_user(user: User, user_db : Session = Depends(get_userdb)):
    existing_user = get_user(user.user_id, user_db)
    if existing_user:
        raise HTTPException(status_code=409, detail="해당 아이디는 이미 존재합니다")
    existing_user_name = get_user_nickname(user.nickname, user_db)
    if existing_user_name:
        raise HTTPException(status_code=409, detail="해당 닉네임은 이미 존재합니다")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(user_id=user.user_id, hashed_password=hashed_password, name=user.name,\
                    nickname=user.nickname, email = user.email, is_mentor = user.is_mentor)
    user_db.add(db_user)
    user_db.commit()
    user_db.refresh(db_user)

    return db_user