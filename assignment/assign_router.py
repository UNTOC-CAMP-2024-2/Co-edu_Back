from fastapi import APIRouter, HTTPException, Depends,Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from assignment.assign_func import *
from assignment.assign_model import *
from assignment.assign_schema import *
from assignment.assign_db import *
from user.user_func import *
from user.user_db import *

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


@router.post("/create") #class id, 내용, 제목 
async def create_assign(data : Assignment,credentials: HTTPAuthorizationCredentials = Security(security),as_db : Session=Depends(get_asdb), user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
#assignment 생성

# token = credentials.credentials
#     user = token_decode(token)
#     check_mentor(user, user_db)
#     new_code = None
#     while new_code == None:
#         new_code = str(random.randint(10000,99999))
#         new_code = check_code(new_code,cs_db)
#     cs_data = Classroom(class_name = data.class_name, class_code = new_code, description = data.description,
#                      max_member = data.max_mameber,created_by = user)
    
#     cs_db.add(cs_data)
#     cs_db.add(usercs_data)
#     cs_db.commit()
#     cs_db.refresh(cs_data)
#     cs_db.refresh(usercs_data)
#     return {"class_name" : data.class_name, "code": new_code, "created_by" : user}          
# 

@router.post("/status/mentor")
#assignment id 에 따른 타입에 따른 반환 필요한거 -> assignment_id
#classroom 정원 가져오기 -> feedback 개수 세기(함수화)
@router.post("/status/mentee")
#assignment id에 따른 반환 -> assignment_id, user_id, feedback 반환
@router.post("/submit")
def submit():
 pass
#assignmet id, user id, answer, test case 제공시 testcasedb들어가 일치 / 불일치 하고 correct/uncorrect 하기
@router.post("/feedback")
#assignmnet id + user_id + feedback 내용 -> feedback db에 저장
def feedback():