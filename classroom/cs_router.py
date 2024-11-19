from fastapi import APIRouter, HTTPException, Depends,Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from user.user_db import get_userdb
from user.user_model import User,VerifiedEmail
from user.user_func import *
from user.user_schema import *
import random
import datetime

from classroom.cs_model import Classroom,UserToClass
from classroom.cs_schema import *
from classroom.cs_func import *
from classroom.cs_db import get_csdb

from user.user_func import *
from user.user_db import get_userdb

import random

security = HTTPBearer()


router = APIRouter(
    prefix="/classroom",
)

@router.post("/create")
def create_classroom(data: NewClassroom,credentials: HTTPAuthorizationCredentials = Security(security),cs_db : Session=Depends(get_csdb), user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_mentor(user, user_db)
    new_code = create_code(cs_db)
    cs_data = Classroom(class_name = data.class_name, class_code = new_code, description = data.description,
                     max_member = data.max_mameber,day = data.day, start_time = data.start_time, 
                     end_time = data.end_time,
                     is_access = data.is_access, is_free = data.is_free, created_by = user, current_member = 1)
    usercs_data = UserToClass(user_id = user, class_code = new_code)
    
    cs_db.add(cs_data)
    cs_db.add(usercs_data)
    cs_db.commit()
    cs_db.refresh(cs_data)
    cs_db.refresh(usercs_data)
    return {"class_name" : data.class_name, "code": new_code, "created_by" : user}
  
@router.delete("/delete")
def delete_classroom(data: ClassroomCode,credentials: HTTPAuthorizationCredentials = Security(security),cs_db : Session=Depends(get_csdb), user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_mentor(user, user_db)
    classroom_data = cs_db.query(Classroom).filter(Classroom.class_code == data.class_code).first()
    userclass_data = cs_db.query(UserToClass).filter(UserToClass.class_code == data.class_code).all()
    if classroom_data is None:
        raise HTTPException(status_code=404, detail="존재하는 클래스룸이 없습니다.")
    if classroom_data.created_by == user:
        cs_db.delete(classroom_data)
        for user_class in userclass_data:
            cs_db.delete(user_class)
        cs_db.commit()
        return "성공적으로 클래스룸이 삭제되었습니다."
    else:
        raise HTTPException(status_code=400, detail="해당 클래스룸을 생성한 멘토가 아닙니다.")
    
@router.put("/join")
def join_classroom(data : ClassroomCode, credentials: HTTPAuthorizationCredentials = Security(security),cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_member(user,data.class_code,cs_db)
    usercs_data = UserToClass(user_id = user, class_code = data.class_code)
    classroom_data = cs_db.query(Classroom).filter(Classroom.class_code == data.class_code).first()
    classroom_data.current_member += 1
    cs_db.add(usercs_data)
    cs_db.commit()
    cs_db.refresh(classroom_data)
    return "정상적으로 해당 클래스룸에 입장하셨습니다."

@router.delete("/leave")
def leave_classroom(data : ClassroomCode, credentials: HTTPAuthorizationCredentials = Security(security),cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    
    
    

    