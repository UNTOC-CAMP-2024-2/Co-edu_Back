from fastapi import APIRouter, HTTPException, Depends,Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from classroom.cs_model import Classroom,UserToClass
from classroom.cs_schema import NewClassroom
from classroom.cs_func import *

from user.user_func import *
from user.user_db import get_userdb


security = HTTPBearer()


router = APIRouter(
    prefix="/classroom",
)

@router.post("/create")
async def create_classroom(data: NewClassroom,credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    user_id = token_decode(token)
    check_mentor(user_id)