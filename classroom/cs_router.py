from fastapi import APIRouter, HTTPException, Depends,Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from user.user_db import get_userdb
from user.user_func import *
from user.user_schema import *

from classroom.cs_model import *
from classroom.cs_schema import *
from classroom.cs_func import *
from classroom.cs_db import get_csdb

from user.user_func import *
from user.user_db import get_userdb
from sqlalchemy import and_
from typing import List

from assignment.assign_db import get_asdb
from assignment.assign_model import AssignmentCategory
security = HTTPBearer()


router = APIRouter(
    prefix="/classroom",
)

@router.post("/create", summary="클래스룸 생성")
def create_classroom(data: NewClassroom,credentials: HTTPAuthorizationCredentials = Security(security),cs_db : Session=Depends(get_csdb), user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    new_code = create_code(cs_db)
    cs_data = Classroom(class_name = data.class_name, class_code = new_code, description = data.description,
                     max_member = data.max_member,day = data.day, start_time = data.start_time, 
                     end_time = data.end_time,
                     is_access = data.is_access, is_free = data.is_free,link = data.link, created_by = user, current_member = 1)
    usercs_data = UserToClass(user_id = user, class_code = new_code)
    
    cs_db.add(cs_data)
    cs_db.add(usercs_data)
    cs_db.commit()
    cs_db.refresh(cs_data)
    cs_db.refresh(usercs_data)
    return {"class_name" : data.class_name, "class_code": new_code, "created_by" : user, "day" : data.day, "start_time" : data.start_time , "end_time" : data.end_time}
  
@router.delete("/delete", summary="클래스룸 삭제")
def delete_classroom(data: ClassroomCode,credentials: HTTPAuthorizationCredentials = Security(security),cs_db : Session=Depends(get_csdb), user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
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
    
@router.put("/join", summary="클래스룸 입장")
def join_classroom(data: ClassroomCode, credentials: HTTPAuthorizationCredentials = Security(security), cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    classroom_data = cs_db.query(Classroom).filter(Classroom.class_code == data.class_code).first()
    
    if not classroom_data:
        raise HTTPException(status_code=404, detail="존재하지 않는 클래스룸입니다.")
    a = check_member(user, data.class_code, cs_db)
    # 무료 여부 확인
    if not classroom_data.is_free:
        # 이미 승인 대기 중인지 확인
        pending = cs_db.query(PendingApproval).filter(
            PendingApproval.user_id == user,
            PendingApproval.class_code == data.class_code
        ).first()
        
        if pending:
            raise HTTPException(status_code=400, detail="이미 승인 대기 중입니다.")
        
        # 승인 대기로 추가
        new_pending = PendingApproval(
            user_id=user,
            class_code=data.class_code,
            requested_at="test"
        )
        cs_db.add(new_pending)
        cs_db.commit()
        return False #승인대기로 넘어감을 의미
    

    usercs_data = UserToClass(user_id=user, class_code=data.class_code)
    if classroom_data.max_member > classroom_data.current_member:
        classroom_data.current_member += 1
        cs_db.add(usercs_data)
        cs_db.commit()
        cs_db.refresh(classroom_data)
        return True, classroom_data  #자유가입일시 바로입장
    else:
        raise HTTPException(status_code=400, detail="이미 인원이 가득찬 클래스룸입니다.")

#해당클래스룸 만든이 일때 안된다는거 작업해야함
@router.delete("/leave" , summary="클래스룸 퇴장")
def leave_classroom(data: ClassroomCode, credentials: HTTPAuthorizationCredentials = Security(security), cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    
    # 수정: and_()를 사용하여 조건 정확히 필터링
    usertoclass = cs_db.query(UserToClass).filter(
        and_(UserToClass.user_id == user, UserToClass.class_code == data.class_code)
    ).first()
    
    if usertoclass:
        cs_db.delete(usertoclass)  # UserToClass 삭제
        classroom_data = cs_db.query(Classroom).filter(Classroom.class_code == data.class_code).first()
        
        if classroom_data:
            classroom_data.current_member -= 1  # current_member 감소
        cs_db.commit()
        return "정상적으로 해당 클래스룸에서 퇴장하셨습니다."
    else:
        raise HTTPException(status_code=404, detail="해당 클래스룸을 찾을 수 없거나 해당 클래스룸에서 유저를 찾을 수 없습니다.")
        

@router.delete("/kick_user", summary="유저 강퇴하기")
def kick_user(data: KickUserForm,
              credentials: HTTPAuthorizationCredentials = Security(security),
              cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)

    # 현재 유저가 해당 클래스룸의 스터디장인지 확인
    classroom_data = cs_db.query(Classroom).filter(
        Classroom.class_code == data.class_code,
        Classroom.created_by == user
    ).first()
    
    if not classroom_data:
        raise HTTPException(status_code=403, detail="해당 클래스룸의 스터디장이 아닙니다.")
    
    # 자기 자신을 강퇴하려는 경우 확인
    if data.kick_user == user:
        raise HTTPException(status_code=400, detail="스터디장은 자기 자신을 강퇴할 수 없습니다.")

    # 강퇴하려는 유저가 해당 클래스룸에 속해 있는지 확인
    user_to_class = cs_db.query(UserToClass).filter(
        UserToClass.user_id == data.kick_user,
        UserToClass.class_code == data.class_code
    ).first()
    
    if not user_to_class:
        raise HTTPException(status_code=404, detail="강퇴하려는 유저가 해당 클래스룸에 속해 있지 않습니다.")

    # 강퇴 처리
    cs_db.delete(user_to_class)

    # 클래스룸의 현재 인원 수 감소
    classroom_data.current_member -= 1

    cs_db.commit()  # 변경사항 반영

    return {"detail": f"유저 {data.kick_user}가 성공적으로 강퇴되었습니다."}
    
@router.get("/myclassroom", response_model=List[ClassroomInfo], summary="내가 속한 클래스룸 확인하기")
def show_myclassroom(credentials: HTTPAuthorizationCredentials = Security(security), cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    usertoclass = cs_db.query(UserToClass).filter(UserToClass.user_id == user).all()
    class_codes = [utc.class_code for utc in usertoclass]
    db_classrooms = cs_db.query(Classroom).filter(Classroom.class_code.in_(class_codes)).all()
    
    return map_classrooms(db_classrooms)  

@router.get("/search_classroom", response_model=List[ClassroomInfo], summary="공개 클래스룸 검색하기")
def search_classroom(search: str = None, cs_db: Session = Depends(get_csdb)):
    query = cs_db.query(Classroom).filter(Classroom.is_access == True)
    
    if search:
        query = query.filter(Classroom.class_name.like(f"%{search}%"))
    
    db_classrooms = query.all()
    return map_classrooms(db_classrooms)  


@router.post("/approve" , summary="입장대기중인 멤버 승인하기")
def approve_member(data: ApprovalRequest, credentials: HTTPAuthorizationCredentials = Security(security), cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    
    # 해당 유저가 스터디장인지 확인
    classroom_data = cs_db.query(Classroom).filter(
        Classroom.class_code == data.class_code,
        Classroom.created_by == user
    ).first()
    if not classroom_data:
        raise HTTPException(status_code=403, detail="해당 클래스룸의 스터디장이 아닙니다.")
    
    pending = cs_db.query(PendingApproval).filter(
        PendingApproval.user_id == data.user_id,
        PendingApproval.class_code == data.class_code
    ).first()
    
    if not pending:
        raise HTTPException(status_code=404, detail="승인 대기 중인 사용자를 찾을 수 없습니다.")
    
    if classroom_data.max_member > classroom_data.current_member:
        # 승인 처리
        new_member = UserToClass(user_id=data.user_id, class_code=data.class_code)
        classroom_data.current_member += 1
        cs_db.add(new_member)
        cs_db.delete(pending)
        cs_db.commit()
        return "승인이 완료되었습니다."
    else:
        raise HTTPException(status_code=400, detail="이미 인원이 가득찬 클래스룸입니다.")
@router.delete("/deny" , summary="입장대기중인 멤버 거절하기")
def deny_member(data: ApprovalRequest, credentials: HTTPAuthorizationCredentials = Security(security), cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    
    # 해당 유저가 스터디장인지 확인
    classroom_data = cs_db.query(Classroom).filter(
        Classroom.class_code == data.class_code,
        Classroom.created_by == user
    ).first()
    if not classroom_data:
        raise HTTPException(status_code=403, detail="해당 클래스룸의 스터디장이 아닙니다.")
    
    pending = cs_db.query(PendingApproval).filter(
        PendingApproval.user_id == data.user_id,
        PendingApproval.class_code == data.class_code
    ).first()
    
    if not pending:
        raise HTTPException(status_code=404, detail="승인 대기 중인 사용자를 찾을 수 없습니다.")
    
    cs_db.delete(pending)
    cs_db.commit()  # 변경 사항을 DB에 반영
    
    return {"detail": "사용자가 성공적으로 거절되었습니다."}
    
@router.get("/class_info", summary="클래스룸 정보확인")
def class_info(class_code : str
               , credentials: HTTPAuthorizationCredentials = Security(security)
               , cs_db: Session = Depends(get_csdb)
               , as_db: Session = Depends(get_asdb)):
    token = credentials.credentials
    user = token_decode(token)
    classroom_data = cs_db.query(Classroom).filter(
        Classroom.class_code == class_code,
    ).first()
    if not classroom_data:
        raise HTTPException(status_code=404, detail="클래스룸 존재하지않음")
    usertoclass = cs_db.query(UserToClass).filter(
        and_(UserToClass.user_id == user, UserToClass.class_code == class_code)
    ).first()

    categories = as_db.query(AssignmentCategory).filter(AssignmentCategory.class_id == class_code).all()
    if usertoclass:
        if classroom_data.created_by != user:
            return classroom_data ,categories, False
        else:
            return classroom_data , categories, True
    else:
        raise HTTPException(status_code=404, detail="해당 크래스룸에 들어가있지 않습니다.")

    
@router.get("/show_edit", summary="설정부분 정보불러오기")
def show_edit(class_code : str
              , credentials: HTTPAuthorizationCredentials = Security(security)
                , cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)

    classroom_data = cs_db.query(Classroom).filter(
        Classroom.class_code == class_code,
        Classroom.created_by == user
    ).first()
    if not classroom_data:
        raise HTTPException(status_code=403, detail="해당 클래스룸의 스터디장이 아닙니다.")
    
    usertoclass = cs_db.query(UserToClass).filter(
        and_(UserToClass.class_code == class_code)
    ).all()

    pending_approvals = cs_db.query(PendingApproval).filter(PendingApproval.class_code == class_code).all()
    return {"class_info" : classroom_data, "user_info" : usertoclass, "approval" : [PendingApprovalInfo(user_id=pa.user_id, class_code=pa.class_code, requested_at=pa.requested_at) for pa in pending_approvals]}

@router.patch("/edit_classinfo", summary="클래스룸 정보 수정하기")
def edit_classinfo(data: UpdateClassroomInfoRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)

    # 수정하려는 클래스룸이 현재 사용자에 의해 생성된 것인지 확인
    classroom = cs_db.query(Classroom).filter(
        Classroom.class_code == data.class_code,
        Classroom.created_by == user
    ).first()
    
    if not classroom:
        raise HTTPException(status_code=403, detail="해당 클래스룸을 수정할 권한이 없습니다.")


    update_fields = {
        "class_name": data.class_name,
        "description": data.description,
        "max_member": data.max_member,
        "day": data.day,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "is_access": data.is_access,
        "is_free": data.is_free,
        "link": data.link,
    }
    for key, value in update_fields.items():
        if value is not None: 
            setattr(classroom, key, value)

    cs_db.commit()

    return {"detail": "클래스룸 정보가 성공적으로 수정되었습니다."}