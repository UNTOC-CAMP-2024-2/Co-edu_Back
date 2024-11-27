from fastapi import APIRouter, HTTPException, Depends,Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from assignment.assign_func import *
from assignment.assign_model import *
from assignment.assign_schema import *
from assignment.assign_db import *
from classroom.cs_func import *
from user.user_func import *
from user.user_db import *
import random

security = HTTPBearer()


router = APIRouter(
    prefix="/assign",
)


"""""
멘티 페이지에서의 Assignment컴포넌트의 type
전체 과제 -> done / undone
내가 제출한 과제 -> done
패드백 모아보기 -> gotFeedback

멘토 페이지에서의 Assignment컴포넌트의 type
전체 과제 -> done / undone / halfDone (멘티들이 다 했는지에 따라)
패드백 모아보기 -> gaveFeedbackAll / gaveFeedbackFew / notGaveFeedbackAll (모든 멘티에게 피드백을 주었는지에 따라)
"""""

#assignment 생성
@router.post("/create") #class id, 내용, 제목 
def create_assign(data : AssignmentCreate,credentials: HTTPAuthorizationCredentials = Security(security),as_db : Session=Depends(get_asdb), user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    new_id = None
    while new_id == None:
        new_id = str(random.randint(10000,99999))
        new_id = check_id(new_id,as_db)

    new_assign =Assignment(assignment_id = new_id, class_id = data.class_id, title = data.title, description = data.description, created_at = datetime.utcnow, deadline = data.deadline,testcase = [],created_by = user)
    as_db.add(new_assign)
    as_db.commit()
    as_db.refresh(new_assign)
    return {"status" : "과제가 정상적으로 생성되었습니다.","assignment_id": new_id}
@router.post("/delete") #assignment delete
def delete_assign(data : DeleteAssign, credentials: HTTPAuthorizationCredentials = Security(security),as_db : Session=Depends(get_asdb),user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_mentor(user, user_db)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else:
        if user == assignment.created_by :
            as_db.delete(assignment)
            as_db.commit()
            return "성공적으로 과제가 삭제되었습니다."
        else :
            return HTTPException(status_code=400, detail="과제를 생성한 유저가 아닙니다.")

#@router.post("/testcase")
#testcase 랑 코드 실행 부분은 나중에 추가할것

@router.post("/class_assignments") # class id에 해당하는 assignments들을 반환
def info(data : GetAssign, credentials: HTTPAuthorizationCredentials = Security(security),as_db : Session=Depends(get_asdb)):
    assignment = as_db.query(Assignment).filter(Assignment.class_id == data.class_id).all()
    return [{"assignment_id":amt.assignment_id,"title":amt.title,"description":amt.description,"created_time":amt.created_at,"deadline":amt.deadline} for amt in assignment]


#assignment id, 에 따른 타입에 따른 반환 필요한거 -> assignment_id
#classroom 정원 가져오기 -> feedback 개수 세기
@router.post("/status/mentor")
def mentor_status(data : GetAssign, credentials: HTTPAuthorizationCredentials = Security(security),as_db : Session=Depends(get_asdb),user_db: Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_mentor(user, user_db)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    return {"assignment_status" : "done/undone/halfdone", "feedback_status" : "gaveFeedbackAll / gaveFeedbackFew / notGaveFeedbackAll"}
    
# @router.post("/status/mentee")
# #assignment id에 따른 반환 -> assignment_id, user_id, feedback 반환

# @router.post("/submit")
# def submit():
#   pass #이부분에서 제출과 실행이 이루어져야 함
# #assignmet id, user id, answer, test case 제공시 testcasedb들어가 일치 / 불일치 하고 correct/uncorrect 하기

# @router.post("/feedback")
# #assignmnet id + user_id + feedback 내용 -> feedback db에 저장
# def feedback():

#제출 -> 비교 -> pass or nonepass 정해져야 feedback, mentor status 가능