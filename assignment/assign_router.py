from fastapi import APIRouter, HTTPException, Depends,Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import desc
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
import logging

logger = logging.getLogger("assignment")

security = HTTPBearer()


router = APIRouter(
    prefix="/assign",
)

#assignment 생성
@router.post("/create", summary="과제 생성")
def create_assign(data : AssignmentData
                  ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb),cs_db : Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    new_id = None
    #classid 유무확인
    check_created(user,data.class_id,cs_db)
    category = as_db.query(AssignmentCategory).filter_by(id=data.category_id).first()
    if category is None:
        logger.warning("[assignment][create][POST][fail] user_id=%s, params=%s, status=실패, message=해당 카테고리가 존재하지 않습니다.", user, {"class_id": data.class_id, "category_id": data.category_id})
        raise HTTPException(status_code=404, detail="해당 카테고리가 존재하지 않습니다.")
    
    while new_id == None:
        new_id = str(random.randint(10000,99999))
        new_id = check_id(new_id,as_db)

    new_assign =Assignment(assignment_id = new_id, class_id = data.class_id
                           ,title = data.title, description = data.description
                           ,created_by = user, category_id=data.category_id
                           ,time_limit=float(data.time_limit) if data.time_limit is not None else None)
    #assignment 기본 정보 저장
    #testcase 추가 필요
    as_db.add(new_assign)
    as_db.commit()
    as_db.refresh(new_assign)
    create_testcase(data.testcase,new_id,as_db)
    logger.info("[assignment][create][POST][success] user_id=%s, params=%s, status=성공, message=과제 생성 완료", user, {"class_id": data.class_id, "assignment_id": new_id})
    return {"status" : "과제가 정상적으로 생성되었습니다.","assignment_id": new_id}


#testcase는 리스트로 받아서 쪼개서 저장
@router.post("/modify",summary="과제 수정")
def modify_assign(data : AssignmentModify ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb)):
    token = credentials.credentials
    user = token_decode(token)
    is_assignment_created(user,data.assignment_id,as_db)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    assignment.description = data.description
    assignment.title = data.title
    assignment.category_id = data.category_id
    assignment.time_limit = float(data.time_limit) if data.time_limit is not None else None
    as_db.commit()
    modify_testcase(data.testcase,data.assignment_id,as_db)
    as_db.commit()
    logger.info("[assignment][modify][POST][success] user_id=%s, params=%s, status=성공, message=과제 수정 완료", user, {"assignment_id": data.assignment_id})
    return {"status": "과제 정보가 정상적으로 수정되었습니다."}

@router.delete("/delete") #assignment delete --> 완료
def delete_assign(assignment_id : str
                  ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb)
                  ,cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if assignment == None :
        logger.warning("[assignment][delete][DELETE][fail] user_id=%s, params=%s, status=실패, message=과제가 존재하지 않습니다.", user, {"assignment_id": assignment_id})
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else:
        check_created(user,assignment.class_id,cs_db)
        is_assignment_created(user,assignment_id,as_db) #권한쟁의
        if user == assignment.created_by :
            delete_assignment(db= as_db, assignment=assignment)
            logger.info("[assignment][delete][DELETE][success] user_id=%s, params=%s, status=성공, message=과제 삭제 완료", user, {"assignment_id": assignment_id})
            return "성공적으로 과제가 삭제되었습니다."
        else :
            logger.warning("[assignment][delete][DELETE][fail] user_id=%s, params=%s, status=실패, message=과제 생성자가 아님", user, {"assignment_id": assignment_id})
            return HTTPException(status_code=400, detail="과제를 생성한 유저가 아닙니다.")

@router.get("/info") # assignment 자체의 info
def assign_info(assignment_id : str, as_db : Session=Depends(get_asdb)):
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if assignment == None :
        logger.warning("[assignment][info][GET][fail] params=%s, status=실패, message=과제가 존재하지 않습니다.", {"assignment_id": assignment_id})
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        testcases = (as_db.query(AssignmentTestcase)
                    .filter(AssignmentTestcase.assignment_id == assignment_id).all())
        logger.info("[assignment][info][GET][success] params=%s, status=성공, message=과제 정보 반환", {"assignment_id": assignment_id})
        return {"assignment_id" : assignment_id, "class_id" : assignment.class_id
                ,"title" : assignment.title,"description" : assignment.description
                ,"created_by" : assignment.created_by,"testcases" : testcases, "timelimit":assignment.time_limit }

@router.get("/info_mentee") # assignment 자체의 info 멘티경우
def assign_info(assignment_id : str, as_db : Session=Depends(get_asdb)):
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if assignment == None :
        logger.warning("[assignment][info_mentee][GET][fail] params=%s, status=실패, message=과제가 존재하지 않습니다.", {"assignment_id": assignment_id})
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        testcases = (as_db.query(AssignmentTestcase)
                    .filter(AssignmentTestcase.assignment_id == assignment_id).limit(3).all())
        logger.info("[assignment][info_mentee][GET][success] params=%s, status=성공, message=과제 정보 반환(멘티)", {"assignment_id": assignment_id})
        return {"assignment_id" : assignment_id, "class_id" : assignment.class_id
                ,"title" : assignment.title,"description" : assignment.description
                ,"created_by" : assignment.created_by,"testcases" : testcases, "timelimit":assignment.time_limit}

@router.get("/status/maker/all",summary="멘토 기준 전체 과제 정보 반환")
def mentor_status_all(class_id : str
                  ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb)
                  ,cs_db : Session=Depends(get_csdb)
                  ,user_db : Session=Depends(get_userdb)) :
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    token = credentials.credentials
    user = token_decode(token)
    if classroom is None:
        logger.warning("[assignment][status/maker/all][GET][fail] user_id=%s, params=%s, status=실패, message=존재하지 않는 클래스룸", user, {"class_id": class_id})
        raise HTTPException(status_code=404, detail="존재하는 클래스룸이 없습니다.")
    check_created(user,class_id,cs_db)
    classroom_users = classroom.current_member-1
    members = all_member(class_id,cs_db)[1:]
    assignments = as_db.query(Assignment).filter(Assignment.class_id == class_id).all()
    if assignments == None :
        raise HTTPException(status_code=404, detail="존재하는 과제가 없습니다.")
    result = []
    
    for assignment in assignments:
        submission_list = []
        feedback_list = []

        submissions = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment.assignment_id).all()
        if submissions == [] :
            assignment_status = "undone"
        elif len(submissions) == classroom_users :
            assignment_status = "done"
        else :
            assignment_status = "halfDone" 

        feedbacks = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment.assignment_id).all()
        if feedbacks == [] :
            feedback_status = "notGaveFeedbackAll"
        elif len(feedbacks) == len(submissions) :
            feedback_status = "gaveFeedbackAll"
        else :
            feedback_status = "gaveFeedbackFew"


        for member in members:
            submission = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment.assignment_id,
                                                                  AssignmentSubmission.user_id == member).first()
            if submission == None :
                submission_list.append({"user_id" : member, "name": get_user_name(member, user_db), "status" : False})
            else :
                submission_list.append({"user_id" : member, "name": get_user_name(member, user_db), "code" : submission.code, "correct" : submission.correct
                                        ,"detailed_result" : submission.detailed_result})
            mem_feedback = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment.assignment_id,
                                                                  AssignmentFeedBack.user_id == member).first()
            
            if mem_feedback == None :
                feedback_list.append({"user_id" : member, "name": get_user_name(member, user_db), "feedback" : False})
            else:
                feedback_list.append({"user_id" : member, "name": get_user_name(member, user_db), "feedback" : mem_feedback.feedback})
        
        as_data = {
            "assignment_id" : assignment.assignment_id,
            "title" : assignment.title,
            "description" : assignment.description,
            "assignment_status" : assignment_status
            ,"feedback_status" : feedback_status  
            ,"feedbacks" : feedback_list # user_db에서 멘토 id 받아와서 없으면 false 반환
            ,"submissions" : submission_list}
        result.append(as_data)
    logger.info("[assignment][status/maker/all][GET][success] user_id=%s, params=%s, status=성공, message=전체 과제 정보 반환", user, {"class_id": class_id})
    return result

@router.get("/status/mentee/all",summary="멘티 기준 전체 과제 정보 반환")
def mentee_status_all(class_id : str
                  ,credentials : HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb),
                  cs_db: Session=Depends(get_csdb)):
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    token = credentials.credentials
    user = token_decode(token)
    if classroom is None:
        logger.warning("[assignment][status/mentee/all][GET][fail] user_id=%s, params=%s, status=실패, message=존재하지 않는 클래스룸", user, {"class_id": class_id})
        raise HTTPException(status_code=404, detail="존재하는 클래스룸이 없습니다.")
    assignments = as_db.query(Assignment).filter(Assignment.class_id == class_id).all()
    if assignments == None :
        return HTTPException(status_code=404, detail="클래스룸 내 과제가 존재하지 않습니다.")
    else :
        result = []
        for assignment in assignments :
            submission = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment.assignment_id
                                                                ,AssignmentSubmission.user_id == user).first()
            if submission == None :
                as_data = {"assignment_id" : assignment.assignment_id, "title" : assignment.title, "description" : assignment.description,
                "status" : False}
                result.append(as_data)
            else :
                feedback = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment.assignment_id,
                                                                AssignmentFeedBack.user_id == user).first()
                if feedback == None :
                    pass
                else :
                    feedback = True
                as_data = {"assignment_id" : assignment.assignment_id , "title" : assignment.title
                , "description" : assignment.description
                        , "status" : submission.correct,"code" : submission.code 
                        , "feedback" : feedback}
                result.append(as_data)
    logger.info("[assignment][status/mentee/all][GET][success] user_id=%s, params=%s, status=성공, message=전체 과제 정보 반환(멘티)", user, {"class_id": class_id})
    return result

@router.get("/mentee_return_three", summary= "멘티 기준 상위 3개의 전체 과제/내가 제출한 과제/과제 피드백 상태 반환")
def mentee_return_three(class_id : str,
                        credentials : HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb),
                  cs_db: Session=Depends(get_csdb)):
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    token = credentials.credentials
    user = token_decode(token)
    if classroom is None:
        logger.warning("[assignment][mentee_return_three][GET][fail] user_id=%s, params=%s, status=실패, message=존재하지 않는 클래스룸", user, {"class_id": class_id})
        raise HTTPException(status_code=404, detail="존재하는 클래스룸이 없습니다.")
    assignments = as_db.query(Assignment)\
            .filter(Assignment.class_id == class_id)\
            .order_by(desc(Assignment.id))\
            .all()  #전부 역순으로.
    if assignments == None :
        return HTTPException(status_code=404, detail="클래스룸 내 과제가 존재하지 않습니다.")
    result = []
    al_list = []#전체 과제
    sub_list = []#제출한 과제
    fed_list = [] #피드백 받은 과제
    for assignment in assignments :
        
        #전체 과제 : 그냥 붙이기 제출한 과제 : submission에서 찾기 피드백 과제 : 피드백에서 찾기
        submission = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment.assignment_id
                                                            ,AssignmentSubmission.user_id == user).first()
        feedback = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment.assignment_id,
                                                          AssignmentFeedBack.user_id == user).first()
        if submission == None :
            al_list.append({"assignment_id" : assignment.assignment_id, "title" : assignment.title, "status" : "undone"})
        else :
            al_list.append({"assignment_id" : assignment.assignment_id, "title" : assignment.title, "status" : "done"})
            sub_list.append({"assignment_id": assignment.assignment_id, "title" : assignment.title, "status" : "done"})
        if feedback:
            al_list[-1]["status"] = "getFeedback"
            fed_list.append({"assignment_id" : assignment.assignment_id, "title" : assignment.title, "status" : "getFeedback"})
    logger.info("[assignment][mentee_return_three][GET][success] user_id=%s, params=%s, status=성공, message=멘티 상위 3개 과제/제출/피드백 반환", user, {"class_id": class_id})
    return {"상위 3개 과제" : al_list[:3],"제출한 상위 3개 과제":sub_list[:3],"상위 3개 피드백":fed_list[:3]}

@router.get("/mentor_return_three", summary= "멘토 기준 상위 3개의 전체 과제/과제 피드백 반환")
def mentee_return_three(class_id : str,
                        credentials : HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb),
                  cs_db: Session=Depends(get_csdb)):
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    token = credentials.credentials
    user = token_decode(token)
    check_created(user,class_id,cs_db)
    if classroom is None:
        logger.warning("[assignment][mentor_return_three][GET][fail] user_id=%s, params=%s, status=실패, message=존재하지 않는 클래스룸", user, {"class_id": class_id})
        raise HTTPException(status_code=404, detail="존재하는 클래스룸이 없습니다.")
    
    al_list = []#완료 상태 표시(전체 과제에서)
    fed_list = [] #피드백 상태 표시(전체 과제에서)
    classroom_users = classroom.current_member-1
    
    assignments = as_db.query(Assignment)\
            .filter(Assignment.class_id == class_id)\
            .order_by(desc(Assignment.id))\
            .all()  #전부 역순으로.
    
    if assignments == None :
        return HTTPException(status_code=404, detail="클래스룸 내 과제가 존재하지 않습니다.")
    
    for assignment in assignments :
        
        submissions = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment.assignment_id).all()

        if submissions == [] :
            assignment_status = "undone"
        elif len(submissions) == classroom_users :
            assignment_status = "done"
        else :
            assignment_status = "halfDone"
        al_list.append({
            "assignment_id" : assignment.assignment_id,
            "title" : assignment.title,
            "assignment_status" : assignment_status
        })
        feedbacks = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment.assignment_id).all()

        if feedbacks == [] :
            feedback_status = "notGaveFeedbackAll"
        elif len(feedbacks) == len(submissions) :
            feedback_status = "gaveFeedbackAll"
        else :
            feedback_status = "gaveFeedbackFew"
        fed_list.append({
            "assignment_id" : assignment.assignment_id,
            "title" : assignment.title,
            "feedback_status" : feedback_status
        })
        
    logger.info("[assignment][mentor_return_three][GET][success] user_id=%s, params=%s, status=성공, message=멘토 상위 3개 과제/피드백 반환", user, {"class_id": class_id})
    return {"상위 3개 과제": al_list[:3],"상위 3개 과제 및 피드백 상태": fed_list[:3]}

@router.get("/mysubmission",summary = "내가 제출한 과제 표시")
def mysubmission(class_id : str
                  ,credentials : HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb),
                  cs_db: Session=Depends(get_csdb)):
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    token = credentials.credentials
    user = token_decode(token)
    if classroom is None:
        logger.warning("[assignment][mysubmission][GET][fail] user_id=%s, params=%s, status=실패, message=존재하지 않는 클래스룸", user, {"class_id": class_id})
        raise HTTPException(status_code=404, detail="존재하는 클래스룸이 없습니다.")
    
    assignments = as_db.query(Assignment).filter(Assignment.class_id == class_id).all()
    if assignments == None :
        return HTTPException(status_code=404, detail="클래스룸 내 과제가 존재하지 않습니다.")
    else :
        result = []
        for assignment in assignments :
            submission = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment.assignment_id
                                                                ,AssignmentSubmission.user_id == user).first()
            if submission == None :
                pass
            else :
                feedback = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment.assignment_id,
                                                                AssignmentFeedBack.user_id == user).first()
                if feedback == None :
                    pass
                else :
                    feedback = feedback.feedback
                as_data = {"assignment_id" : assignment.assignment_id , "title" : assignment.title
                        , "status" : submission.correct,"code" : submission.code, "submitted_at" : submission.submitted_at
                        , "feedback" : feedback}
                result.append(as_data)
    logger.info("[assignment][mysubmission][GET][success] user_id=%s, params=%s, status=성공, message=내가 제출한 과제 반환", user, {"class_id": class_id})
    return result

@router.get("/myfeedbacks",summary="받은 피드백 표시")
def myfeedbacks(class_id : str
                  ,credentials : HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb),
                  cs_db: Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    if classroom == None :
        logger.warning("[assignment][myfeedbacks][GET][fail] user_id=%s, params=%s, status=실패, message=존재하지 않는 클래스룸", user, {"class_id": class_id})
        raise HTTPException(status_code=404, detail="클래스룸이 존재하지 않습니다.")
    assignments = as_db.query(Assignment).filter(Assignment.class_id == class_id)
    result = []
    for assignment in assignments:
        feedback = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment.assignment_id,
                                                            AssignmentFeedBack.user_id == user).first()
        if feedback == None:
            pass
        else:
            data = {"assignment_id" : assignment.assignment_id, "title" : assignment.title , "feedback" : feedback.feedback}
            result.append(data)
    logger.info("[assignment][myfeedbacks][GET][success] user_id=%s, params=%s, status=성공, message=받은 피드백 반환", user, {"class_id": class_id})
    if result == []:
        return "받은 피드백이 없습니다."
    else :
        return result

@router.get("/status/maker" , summary="멘토 기준 개별 과제에 대한 status 반환") #
def mentor_status(assignment_id : str
                  ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb)
                  ,user_db: Session=Depends(get_userdb)
                  ,cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if assignment == None :
        logger.warning("[assignment][status/maker][GET][fail] user_id=%s, params=%s, status=실패, message=과제가 존재하지 않습니다.", user, {"assignment_id": assignment_id})
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        check_created(user,assignment.class_id,cs_db)
        is_assignment_created(user,assignment_id,as_db)
        
        class_id = assignment.class_id
        classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
        classroom_users = classroom.current_member-1
        members = all_member(class_id,cs_db)[1:]
        submissions = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id).all()

        if submissions == [] :
            assignment_status = "undone"
        elif len(submissions) == classroom_users :
            assignment_status = "done"
        else :
            assignment_status = "halfDone"

        feedbacks = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment_id).all()

        if feedbacks == [] :
            feedback_status = "notGaveFeedbackAll"
        elif len(feedbacks) == len(submissions) :
            feedback_status = "gaveFeedbackAll"
        else :
            feedback_status = "gaveFeedbackFew"

        submission_list = []
        feedback_list = []

        for member in members:
            submission = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment.assignment_id,
                                                                  AssignmentSubmission.user_id == member).first()
            if submission == None :
                submission_list.append({"user_id" : member,"status" : False})
            else :
                submission_list.append({"user_id" : member,"status" : True , "code" : submission.code, "correct" : submission.correct
                                        ,"detailed_result" : submission.detailed_result, "submitted_at" : submission.submitted_at})
            mem_feedback = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment.assignment_id,
                                                                  AssignmentFeedBack.user_id == member).first()
            
            if mem_feedback == None :
                feedback_list.append({"user_id" : member, "feedback" : False})
            else:
                feedback_list.append({"user_id" : member, "feedback" : mem_feedback.feedback})

        logger.info("[assignment][status/maker][GET][success] user_id=%s, params=%s, status=성공, message=멘토 개별 과제 status 반환", user, {"assignment_id": assignment_id})
        return {"assignment_status" : assignment_status
                ,"feedback_status" : feedback_status
                ,"feedbacks" : feedback_list
                ,"submissions" : submission_list}



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
        logger.warning("[assignment][status/mentee][GET][fail] user_id=%s, params=%s, status=실패, message=과제가 존재하지 않습니다.", user, {"assignment_id": assignment_id})
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        submission = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id
                                                              ,AssignmentSubmission.user_id == user).first()
        if submission == None :
            logger.warning("[assignment][status/mentee][GET][fail] user_id=%s, params=%s, status=실패, message=제출 이력이 없습니다.", user, {"assignment_id": assignment_id})
            return HTTPException(status_code=404, detail="제출 이력이 없습니다.")
        feedback = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment_id,
                                                          AssignmentFeedBack.user_id == user).first()
        logger.info("[assignment][status/mentee][GET][success] user_id=%s, params=%s, status=성공, message=멘티 개별 과제 status 반환", user, {"assignment_id": assignment_id})
        return {"assignment_id" : assignment_id, "user_id" : user
                , "status" : submission.correct,"code" : submission.code, "submitted_at" : submission.submitted_at
                , "feedback" : feedback}


@router.get("/class_assignments") # class id에 해당하는 전체 assignments들을 반환 
def info(class_id : str, as_db : Session=Depends(get_asdb),cs_db : Session=Depends(get_csdb)):
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    if classroom == None :
        logger.warning("[assignment][class_assignments][GET][fail] params=%s, status=실패, message=클래스룸이 존재하지 않습니다.", {"class_id": class_id})
        return HTTPException(status_code=404, detail="클래스룸이 존재하지 않습니다.")
    else :
        assignments = as_db.query(Assignment).filter(Assignment.class_id == class_id).all()
        logger.info("[assignment][class_assignments][GET][success] params=%s, status=성공, message=전체 assignments 반환", {"class_id": class_id})
        return [amt for amt in assignments]

#해야 되는 과제 라우터 : 이름 반환 + 했는지 안했는지 ~
@router.get("/tasks")
def tasks(credentials : HTTPAuthorizationCredentials = Security(security)
             ,as_db : Session=Depends(get_asdb)
             ,cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    usertoclass = cs_db.query(UserToClass).filter(UserToClass.user_id == user).all()
    class_codes = [utc.class_code for utc in usertoclass]
    
    results = []

    for class_id in class_codes:
        assignment_stats = []

        assignments = as_db.query(Assignment).filter(Assignment.class_id == class_id).all()
        for assign in assignments:
            id = assign.assignment_id
            submission = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == id).first()
            if submission == None:
                stats = "제출안함" 
            elif submission.correct == True:
                stats = "정답"
            elif submission.correct == False:
                stats = "틀림"
            assignment_stats.append(f"{id} : {stats}")
        # 문자열로 추가
        results.append(f"{class_id} : {assignment_stats}")
    
    logger.info("[assignment][tasks][GET][success] user_id=%s, status=성공, message=해야 되는 과제 리스트 반환", user)
    return {"클래스룸 : [과제 : 제출여부]" :results}


@router.post("/feedback")
#assignmnet id + user_id + feedback 내용 -> feedback db에 저장
def feedback(data : Feedback
             ,credentials : HTTPAuthorizationCredentials = Security(security)
             ,as_db : Session=Depends(get_asdb)
             ,cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    if assignment == None :
        logger.warning("[assignment][feedback][POST][fail] user_id=%s, params=%s, status=실패, message=과제가 존재하지 않습니다.", user, {"assignment_id": data.assignment_id})
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        is_assignment_created(user,data.assignment_id,as_db)
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
            logger.info("[assignment][feedback][POST][success] user_id=%s, params=%s, status=성공, message=피드백 추가", user, {"assignment_id": data.assignment_id, "mentee_id": data.mentee_id})
            return {"status" : "성공","feedback" : data.feedback}
        else :
            as_db.delete(feedback)
            new_feedback = AssignmentFeedBack(assignment_id = data.assignment_id,
                                              user_id = data.mentee_id)
            as_db.add(new_feedback)
            as_db.commit()
            as_db.refresh(new_feedback)
            logger.info("[assignment][feedback][POST][success] user_id=%s, params=%s, status=성공, message=피드백 갱신", user, {"assignment_id": data.assignment_id, "mentee_id": data.mentee_id})
            return {"status" : "새 피드백을 추가했습니다.", "feedback" : data.feedback}


@router.post("/submit") #코드 는 제출만(json파싱된다는가정하에)
def submit(data : Submit
           ,credentials : HTTPAuthorizationCredentials = Security(security)
           ,as_db : Session=Depends(get_asdb)
           ,cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    if assignment is None:
        logger.warning("[assignment][submit][POST][fail] user_id=%s, params=%s, status=실패, message=과제가 존재하지 않습니다.", user, {"assignment_id": data.assignment_id})
        raise HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    testcases = as_db.query(AssignmentTestcase).filter(
        AssignmentTestcase.assignment_id == data.assignment_id
    ).all()
    if not testcases:
        logger.warning("[assignment][submit][POST][fail] user_id=%s, params=%s, status=실패, message=테스트케이스가 존재하지 않습니다.", user, {"assignment_id": data.assignment_id})
        raise HTTPException(status_code=400, detail="테스트케이스가 존재하지 않습니다.")
    results, detailed_result, total_score = execute_tests_and_get_results(data.language, data.code, testcases, assignment.time_limit)
    old_submission = as_db.query(AssignmentSubmission)\
        .filter(AssignmentSubmission.assignment_id == data.assignment_id
                ,AssignmentSubmission.user_id == user).first()
    if old_submission :
        as_db.delete(old_submission)
    submission = AssignmentSubmission( 
        user_id=user,
        assignment_id=data.assignment_id,
        code=data.code,
        correct=all(result["result"] == "Pass" for result in results),
        detailed_result=detailed_result,
        submitted_at=returnnow(),
        language=data.language
    )
    as_db.add(submission)
    as_db.commit()
    logger.info("[assignment][submit][POST][success] user_id=%s, params=%s, status=성공, message=과제 제출 완료", user, {"assignment_id": data.assignment_id})
    return {
        "status": "제출 완료."
    }




@router.post("/test_assignment") #테스트 필요
async def test_assignment(data: Test,
                          credentials: HTTPAuthorizationCredentials = Security(security),
                          as_db: Session = Depends(get_asdb),
                          cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    if assignment is None:
        logger.warning("[assignment][test_assignment][POST][fail] user_id=%s, params=%s, status=실패, message=과제가 존재하지 않습니다.", user, {"assignment_id": data.assignment_id})
        raise HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    testcases = as_db.query(AssignmentTestcase).filter(
        AssignmentTestcase.assignment_id == data.assignment_id
    ).all()
    if not testcases:
        logger.warning("[assignment][test_assignment][POST][fail] user_id=%s, params=%s, status=실패, message=테스트케이스가 존재하지 않습니다.", user, {"assignment_id": data.assignment_id})
        raise HTTPException(status_code=400, detail="테스트케이스가 존재하지 않습니다.")
    results, detailed_result, total_score = execute_tests_and_get_results(data.language, data.code, testcases, assignment.time_limit)
    logger.info("[assignment][test_assignment][POST][success] user_id=%s, params=%s, status=성공, message=테스트 완료", user, {"assignment_id": data.assignment_id})
    return {
        "status": "테스트가 완료되었습니다.",
        "results": results,
        "total_score": total_score,
        "is_correct": all(result["result"] == "Pass" for result in results)
    }


def execute_tests_and_get_results(language, code, testcases, time_limit=None):
    from assignment.restricted_execution import execute_code

    results = []
    total_tests = len(testcases)
    passed_tests = 0

    for num, testcase in enumerate(testcases):
        input_data = testcase.input
        expected_output = testcase.expected_output

        # 코드 실행 (stdout, stderr, 실행 시간)
        output, error, exec_time_s = execute_code(language, code, input_data, time_limit)

        if error:
            if str(error) == "Execution timed out.":
                raise HTTPException(status_code=400, detail="Execution timed out.")
            results.append({
                "case_number": num + 1,
                "result": "Error",
                "details": str(error),
                "execution_time_s": exec_time_s
            })
        elif output.strip() == expected_output.strip():
            results.append({
                "case_number": num + 1,
                "result": "Pass",
                "execution_time_s": exec_time_s
            })
            passed_tests += 1
        else:
            results.append({
                "case_number": num + 1,
                "result": "Fail",
                "details": f"Expected {expected_output}, but got {output}",
                "execution_time_s": exec_time_s
            })

    # 점수 계산
    total_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    detailed_result = results

    return results, detailed_result, total_score


@router.get("/code_data/{assignment_id}", summary="과제별 자기 코드 불러오기")
def get_code_data(assignment_id : str,
                  credentials: HTTPAuthorizationCredentials = Security(security),
                  as_db: Session = Depends(get_asdb),
                  cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id, AssignmentSubmission.user_id == user).first()
    if assignment:
        logger.info("[assignment][code_data][GET][success] user_id=%s, params=%s, status=성공, message=자기 코드 반환", user, {"assignment_id": assignment_id})
        return {"code" : assignment.code, "language" : assignment.language}
    else:
        logger.warning("[assignment][code_data][GET][fail] user_id=%s, params=%s, status=실패, message=제출내역 없음", user, {"assignment_id": assignment_id})
        return ""
    

@router.post("/category",summary="카테고리 생성")
def create_category(data: Category, credentials: HTTPAuthorizationCredentials = Security(security), as_db: Session = Depends(get_asdb),cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_created(user,data.class_id,cs_db)
    create_new_category(data,as_db)
    logger.info("[assignment][category][POST][success] user_id=%s, params=%s, status=성공, message=카테고리 생성", user, {"class_id": data.class_id})


@router.get("/categories", summary="클래스룸 내 카테고리 목록 조회")
def get_categories(class_id: str,
                   credentials: HTTPAuthorizationCredentials = Security(security),
                   as_db: Session = Depends(get_asdb),cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    if not classroom:
        logger.warning("[assignment][categories][GET][fail] user_id=%s, params=%s, status=실패, message=클래스룸이 존재하지 않습니다.", user, {"class_id": class_id})
        raise HTTPException(status_code=404, detail="해당 클래스룸이 존재하지 않습니다.")
    categories = as_db.query(AssignmentCategory).filter(AssignmentCategory.class_id == class_id).all()
    logger.info("[assignment][categories][GET][success] user_id=%s, params=%s, status=성공, message=카테고리 목록 반환", user, {"class_id": class_id})
    return [{"id": c.id, "name": c.name, "description": c.description} for c in categories]

@router.get("/status/mentee/category/{category_id}", summary="멘티 기준 카테고리별 과제 정보 반환")
def mentee_status_by_category(category_id: int,
                              credentials: HTTPAuthorizationCredentials = Security(security),
                              as_db: Session = Depends(get_asdb),
                              cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    category = as_db.query(AssignmentCategory).filter(AssignmentCategory.id == category_id).first()
    if not category:
        logger.warning("[assignment][status/mentee/category][GET][fail] user_id=%s, params=%s, status=실패, message=카테고리가 존재하지 않습니다.", user, {"category_id": category_id})
        raise HTTPException(status_code=404, detail="해당 카테고리가 존재하지 않습니다.")
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == category.class_id).first()
    if not classroom:
        logger.warning("[assignment][status/mentee/category][GET][fail] user_id=%s, params=%s, status=실패, message=클래스룸이 존재하지 않습니다.", user, {"category_id": category_id})
        raise HTTPException(status_code=404, detail="해당 클래스룸이 존재하지 않습니다.")
    assignments = as_db.query(Assignment).filter(Assignment.category_id == category_id).all()
    if not assignments:
        logger.warning("[assignment][status/mentee/category][GET][fail] user_id=%s, params=%s, status=실패, message=카테고리에 속한 과제가 존재하지 않습니다.", user, {"category_id": category_id})
        raise HTTPException(status_code=404, detail="해당 카테고리에 속한 과제가 존재하지 않습니다.")
    result = []
    for assignment in assignments:
        submission = as_db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == assignment.assignment_id,
            AssignmentSubmission.user_id == user
        ).first()
        feedback = as_db.query(AssignmentFeedBack).filter(
            AssignmentFeedBack.assignment_id == assignment.assignment_id,
            AssignmentFeedBack.user_id == user
        ).first()
        if submission is None:
            as_data = {
                "assignment_id": assignment.assignment_id,
                "title": assignment.title,
                "description": assignment.description,
                "status": False
            }
        else:
            as_data = {
                "assignment_id": assignment.assignment_id,
                "title": assignment.title,
                "description": assignment.description,
                "status": submission.correct,
                "code": submission.code,
                "feedback": bool(feedback)
            }
        result.append(as_data)
    logger.info("[assignment][status/mentee/category][GET][success] user_id=%s, params=%s, status=성공, message=카테고리별 과제 정보 반환", user, {"category_id": category_id})
    return result
