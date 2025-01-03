from sqlalchemy.orm import Session
from user.user_model import User
from passlib.context import CryptContext
from fastapi import HTTPException
from classroom.cs_model import Classroom,UserToClass
import random
from typing import List
from classroom.cs_schema import *

    
def check_created(user_id,class_code, db: Session):
    classroom_data = db.query(Classroom).filter(
        Classroom.class_code == class_code,
        Classroom.created_by == user_id
    ).first()
    if not classroom_data:
        raise HTTPException(status_code=403, detail="해당 클래스룸의 스터디장이 아닙니다.")
#해당 클래스룸에 존재하는 유저인지 판별
def check_member(user_id,class_code, db: Session):
    data = db.query(UserToClass).filter(UserToClass.user_id == user_id).all()
    if class_code in data:
        raise HTTPException(status_code=409, detail="이미 가입된 스터디방입니다.")
    else:
        return
    
#랜덤코드 발급시 중복확인
def check_code(code, db: Session):
    data = db.query(Classroom).filter(Classroom.class_code == code).first()
    if data:
        return None
    else:
        return code

#랜덤코드생성
def create_code(db: Session):
    new_code = None
    while new_code == None:
        new_code = str(random.randint(10000,99999))
        new_code = check_code(new_code,db)
    return new_code

# Classroom 객체를 변환하는 공통 함수
def map_classrooms(db_classrooms: List[ClassroomInfo]) -> List[ClassroomInfo]:
    return [
        Classroom(
            class_name=db_classroom.class_name,
            description=db_classroom.description,
            max_member=db_classroom.max_member,
            current_member=db_classroom.current_member,
            day=db_classroom.day,
            start_time=db_classroom.start_time,
            end_time=db_classroom.end_time,
            link = db_classroom.link
        ) for db_classroom in db_classrooms
    ]