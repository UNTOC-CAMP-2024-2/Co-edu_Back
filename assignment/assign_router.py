from fastapi import APIRouter, HTTPException, Depends,Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from assignment.assign_func import *
from assignment.assign_model import *
from assignment.assign_schema import *
from assignment.assign_db import *
from classroom.cs_func import *
from classroom.cs_db import get_csdb
from classroom.cs_model import *
from user.user_func import *
from user.user_db import *
import random

security = HTTPBearer()


router = APIRouter(
    prefix="/assign",
)

#assignment 생성
@router.post("/create") #class id, 내용, 제목 --> 완료
def create_assign(data : AssignmentCreate
                  ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb)
                  ,user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    new_id = None
    #classid 유무확인
    assignment = as_db.query(Classroom).filter(Classroom.class_code == data.class_id).first()
    while new_id == None:
        new_id = str(random.randint(10000,99999))
        new_id = check_id(new_id,as_db)

    new_assign =Assignment(assignment_id = new_id, class_id = data.class_id
                           ,title = data.title, description = data.description
                           ,created_at = datetime.utcnow(), deadline = data.deadline
                           ,created_by = user)
    as_db.add(new_assign)
    as_db.commit()
    as_db.refresh(new_assign)
    return {"status" : "과제가 정상적으로 생성되었습니다.","assignment_id": new_id}

@router.delete("/delete") #assignment delete --> 완료
def delete_assign(data : DeleteAssign
                  ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb)
                  ,user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_mentor(user, user_db)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else:
        if user == assignment.created_by :
            delete_assignment(db= as_db, assignment=assignment)
            return "성공적으로 과제가 삭제되었습니다."
        else :
            return HTTPException(status_code=400, detail="과제를 생성한 유저가 아닙니다.")

@router.get("/info") # assignment 자체의 info
def assign_info(assignment_id : str, as_db : Session=Depends(get_asdb)):
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        testcases = (as_db.query(AssignmentTestcase)
                    .filter(AssignmentTestcase.assignment_id == assignment_id)
                    .order_by(AssignmentTestcase.case_number.asc())
                    .all())
        return {"assignment_id" : assignment_id, "class_id" : assignment.class_id
                ,"title" : assignment.title,"description" : assignment.description
                ,"deadline" : assignment.description,"created_at" : assignment.created_at
                ,"created_by" : assignment.created_by,"testcases" : testcases}


@router.get("/status/mentor") #
def mentor_status(assignment_id : str
                  ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb)
                  ,user_db: Session=Depends(get_userdb)
                  ,cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_mentor(user, user_db)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        class_id = assignment.class_id
        classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
        classroom_users = classroom.current_member
        submissions = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id).all()
        if submissions == [] :
            assignment_status = "undone"
        elif len(submissions) == classroom_users :
            assignment_status = "done"
        else :
            assignment_status = "halfdone"
        feedbacks = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment_id).all()
        if feedbacks == [] :
            feedback_status = "notGaveFeedbackAll"
        elif len(feedbacks) == classroom_users :
            feedback_status = "gaveFeedbackAll"
        else :
            feedback_status = "gaveFeedbackFew"
        
        return {"assignment_status" : assignment_status
                ,"feedback_status" : feedback_status
                ,"feedbacks" : feedbacks}

# #assignment id에 따른 반환 -> 개개인(멘티 전용 과제 상태) assignment_id, user_id, feedback,status,code(제출한) 반환
@router.get("/status/mentee")
def mentee_status(assignment_id : str
                  ,credentials : HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb),
                  user_db: Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        submission = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id
                                                              ,AssignmentSubmission.user_id == user).first()
        if submission == None :
            return HTTPException(status_code=404, detail="제출 이력이 없습니다.")
        feedback = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment_id,
                                                          AssignmentFeedBack.user_id == user).first()
        return {"assignment_id" : assignment_id, "user_id" : user
                , "status" : submission.correct,"code" : submission.code
                , "feedback" : feedback}


@router.post("/testcase") 
def testcase(data : TestCase,credentials: HTTPAuthorizationCredentials = Security(security),
             as_db : Session=Depends(get_asdb),
             user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_mentor(user, user_db)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else:
        if user == assignment.created_by :
            case_number = add_testcase(db = as_db,assignment_id=data.assignment_id,
                         input_data=data.input_data,
                         expected_output=data.expected_output)
            return {"status" : "테스트케이스를 성공적으로 추가했습니다.", "case_number" : case_number}
        else :
            return HTTPException(status_code=400, detail="과제를 생성한 유저가 아닙니다.")
        
@router.delete("/testcasedelete")
def testcasedelete(data : DeleteTestCase,credentials: HTTPAuthorizationCredentials = Security(security),
             as_db : Session=Depends(get_asdb),
             user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_mentor(user, user_db)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else:
        if user == assignment.created_by :
            delete_testcase(db = as_db,assignment_id=data.assignment_id,
                         case_number=data.case_number)
            return "테스트케이스를 성공적으로 삭제했습니다."
        else :
            return HTTPException(status_code=400, detail="과제를 생성한 유저가 아닙니다.")

@router.get("/class_assignments") # class id에 해당하는 전체 assignments들을 반환 
def info(class_id : str, as_db : Session=Depends(get_asdb)):
    assignments = as_db.query(Assignment).filter(Assignment.class_id == class_id).all()
    return [amt.assignment_id for amt in assignments]

@router.post("/submit") #코드 검증 / 틀리고 맞음 기능 없음(추가해야함)
def submit(data : Submit
           ,credentials : HTTPAuthorizationCredentials = Security(security)
           ,as_db : Session=Depends(get_asdb)):
    token = credentials.credentials
    user = token_decode(token)
    
    submission = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.user_id == user).first()
    if submission:
        as_db.delete(submission)
        as_db.refresh(submission) #제출에 코드 넣으니까 json 파싱을 못함
    new_submission = AssignmentSubmission(assignment_id = data.assignment_id,user_id = user
                                      , submitted_at = datetime.utcnow(),code = data.code
                                      , correct = True)
    as_db.add(new_submission)
    as_db.commit()
    as_db.refresh(new_submission)
    return "새 코드 제출을 완료했습니다."

@router.post("/feedback")
#assignmnet id + user_id + feedback 내용 -> feedback db에 저장
def feedback(data : Feedback
             ,credentials : HTTPAuthorizationCredentials = Security(security)
             ,as_db : Session=Depends(get_asdb)
             ,user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_mentor(db=user_db,user_id=user)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).all()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        feedback = as_db.query(AssignmentFeedBack).\
                   filter(AssignmentFeedBack.assignment_id == data.assignment_id,
                          AssignmentFeedBack.user_id == data.mentee_id).first()
        if feedback == None :        
            new_feedback = AssignmentFeedBack(assignment_id = data.assignment_id,
                                              user_id = data.mentee_id
                                              ,feedback = data.feedback)
            as_db.add(new_feedback)
            as_db.commit()
            as_db.refresh(new_feedback)
            return {"status" : "성공","feedback" : data.feedback}
        else :
            as_db.delete(feedback)
            new_feedback = AssignmentFeedBack(assignment_id = data.assignment_id,
                                              user_id = data.mentee_id)
            as_db.add(new_feedback)
            as_db.commit()
            as_db.refresh(new_feedback)
            return {"status" : "새 피드백을 추가했습니다.", "feedback" : data.feedback}
