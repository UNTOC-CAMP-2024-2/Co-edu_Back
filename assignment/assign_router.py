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
@router.post("/create", summary="과제 생성")
def create_assign(data : AssignmentData
                  ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb),cs_db : Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    new_id = None
    #classid 유무확인
    check_created(user,data.class_id,cs_db)
    while new_id == None:
        new_id = str(random.randint(10000,99999))
        new_id = check_id(new_id,as_db)

    new_assign =Assignment(assignment_id = new_id, class_id = data.class_id
                           ,title = data.title, description = data.description
                           ,created_by = user)
    #assignment 기본 정보 저장
    #testcase 추가 필요
    as_db.add(new_assign)
    as_db.commit()
    as_db.refresh(new_assign)
    create_testcase(data.testcase,new_id,as_db)
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
    as_db.commit()
    modify_testcase(data.testcase,data.assignment_id,as_db)
    as_db.commit()
    #과제 정보 수정


@router.delete("/delete") #assignment delete --> 완료
def delete_assign(assignment_id : str
                  ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb)
                  ,cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else:
        check_created(user,assignment.class_id,cs_db)
        is_assignment_created(user,assignment_id,as_db) #권한쟁의
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
                    .filter(AssignmentTestcase.assignment_id == assignment_id).all())
        return {"assignment_id" : assignment_id, "class_id" : assignment.class_id
                ,"title" : assignment.title,"description" : assignment.description
                ,"created_by" : assignment.created_by,"testcases" : testcases}

@router.get("/status/maker/all",summary="멘토 기준 전체 과제 정보 반환")
def mentor_status_all(class_id : str
                  ,credentials: HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb)
                  ,cs_db : Session=Depends(get_csdb)) :
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    token = credentials.credentials
    user = token_decode(token)
    if classroom is None:
        raise HTTPException(status_code=404, detail="존재하는 클래스룸이 없습니다.")
    check_created(user,class_id,cs_db)
    classroom_users = classroom.current_member
    assignments = as_db.query(Assignment).filter(Assignment.class_id == class_id).all()
    if assignments == None :
        raise HTTPException(status_code=404, detail="존재하는 과제가 없습니다.")
    result = []
    for assignment in assignments:
        submissions = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment.assignment_id).all()
        if submissions == [] :
            assignment_status = "undone"
        elif len(submissions) == classroom_users :
            assignment_status = "done"
        else :
            assignment_status = "halfdone"
        feedbacks = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment.assignment_id).all()

        if feedbacks == [] :
            feedback_status = "notGaveFeedbackAll"
        elif len(feedbacks) == len(submissions) :
            feedback_status = "gaveFeedbackAll"
        else :
            feedback_status = "gaveFeedbackFew"
        as_data = {
            "assignment_id" : assignment.assignment_id,
            "title" : assignment.title,
            "assignment_status" : assignment_status
            ,"feedback_status" : feedback_status
            ,"feedbacks" : feedbacks
            ,"submissions" : submissions}
        result.append(as_data)
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
                as_data = {"assignment_id" : assignment.assignment_id, "title" : assignment.title, "status" : "제출 이력이 존재하지 않음"}
                result.append(as_data)
            else :
                feedback = as_db.query(AssignmentFeedBack).filter(AssignmentFeedBack.assignment_id == assignment.assignment_id,
                                                                AssignmentFeedBack.user_id == user).first()
                as_data = {"assignment_id" : assignment.assignment_id , "title" : assignment.title
                        , "status" : submission.correct,"code" : submission.code
                        , "feedback" : feedback}
                result.append(as_data)
    return result
@router.get("/mysubmission",summary = "내가 제출한 과제 표시")
def mysubmission(class_id : str
                  ,credentials : HTTPAuthorizationCredentials = Security(security)
                  ,as_db : Session=Depends(get_asdb),
                  cs_db: Session=Depends(get_csdb)):
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    token = credentials.credentials
    user = token_decode(token)
    if classroom is None:
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
                as_data = {"assignment_id" : assignment.assignment_id , "title" : assignment.title
                        , "status" : submission.correct,"code" : submission.code
                        , "feedback" : feedback.feedback}
                result.append(as_data)
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
        return HTTPException(status_code=404, detail="클래스룸이 존재하지 않습니다.")
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
    if result == []:
        return "받은 피드백이 없습니다."
    else :
        return result

#멘토 멘티 둘다 전체반환 만들기
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
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        check_created(user,assignment.class_id,cs_db)
        is_assignment_created(user,assignment_id,as_db)
        
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
        elif len(feedbacks) == len(submissions) :
            feedback_status = "gaveFeedbackAll"
        else :
            feedback_status = "gaveFeedbackFew"
        
        return {"assignment_status" : assignment_status
                ,"feedback_status" : feedback_status
                ,"feedbacks" : feedbacks
                ,"submissions" : submissions}



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


@router.get("/class_assignments") # class id에 해당하는 전체 assignments들을 반환 
def info(class_id : str, as_db : Session=Depends(get_asdb),cs_db : Session=Depends(get_csdb)):
    classroom = cs_db.query(Classroom).filter(Classroom.class_code == class_id).first()
    if classroom == None :
        return HTTPException(status_code=404, detail="클래스룸이 존재하지 않습니다.")
    else :
        assignments = as_db.query(Assignment).filter(Assignment.class_id == class_id).all()
        return [amt for amt in assignments]

@router.post("/submit") #코드 는 제출만(json파싱된다는가정하에)
def submit(data : Submit
           ,credentials : HTTPAuthorizationCredentials = Security(security)
           ,as_db : Session=Depends(get_asdb)
           ,cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    #classroom 내에 있는지 확인
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    check_member(user,assignment.class_id,cs_db)
    submission = as_db.query(AssignmentSubmission).filter(AssignmentSubmission.user_id == user).first()
    if submission:
        as_db.delete(submission)
        as_db.refresh(submission) #제출에 코드 넣으니까 json 파싱을 못함
    new_submission = AssignmentSubmission(assignment_id = data.assignment_id,user_id = user
                                      , code = data.code
                                      , correct = True)
    as_db.add(new_submission)
    as_db.commit()
    as_db.refresh(new_submission)
    return "새 코드 제출을 완료했습니다."


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
            return {"status" : "성공","feedback" : data.feedback}
        else :
            as_db.delete(feedback)
            new_feedback = AssignmentFeedBack(assignment_id = data.assignment_id,
                                              user_id = data.mentee_id)
            as_db.add(new_feedback)
            as_db.commit()
            as_db.refresh(new_feedback)
            return {"status" : "새 피드백을 추가했습니다.", "feedback" : data.feedback}


@router.post("/test_assignment")
async def test_assignment(data: Test,
                          credentials: HTTPAuthorizationCredentials = Security(security),
                          as_db: Session = Depends(get_asdb),
                          cs_db: Session = Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()

    if assignment is None:
        raise HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")

    # 테스트케이스 가져오기
    testcases = as_db.query(AssignmentTestcase).filter(
        AssignmentTestcase.assignment_id == data.assignment_id
    ).order_by(AssignmentTestcase.case_number.asc()).all()

    if not testcases:
        raise HTTPException(status_code=400, detail="테스트케이스가 존재하지 않습니다.")

    # 테스트 실행 및 결과 저장
    results, detailed_result, total_score = execute_tests_and_get_results(data.language, data.code, testcases)

    # 결과를 AssignmentSubmission 테이블에 저장
    submission = AssignmentSubmission(
        user_id=user,
        assignment_id=data.assignment_id,
        code=data.code,
        correct=all(result["result"] == "Pass" for result in results),
        detailed_result=detailed_result,
    )
    as_db.add(submission)
    as_db.commit()

    return {
        "status": "테스트가 완료되었습니다.",
        "results": results,
        "total_score": total_score,
        "is_correct": all(result["result"] == "Pass" for result in results)
    }


def execute_tests_and_get_results(language,code, testcases):
    from assignment.restricted_execution import execute_code

    results = []
    total_tests = len(testcases)
    passed_tests = 0

    for testcase in testcases:
        input_data = testcase.input
        expected_output = testcase.expected_output

        # 코드 실행
        output, error = execute_code(language, code, input_data)

        if error:
            results.append({
                "case_number": testcase.case_number,
                "result": "Error",
                "details": str(error)
            })
        elif output.strip() == expected_output.strip():
            results.append({
                "case_number": testcase.case_number,
                "result": "Pass"
            })
            passed_tests += 1
        else:
            results.append({
                "case_number": testcase.case_number,
                "result": "Fail",
                "details": f"Expected {expected_output}, but got {output}"
            })

    # 점수 계산
    total_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    detailed_result = results

    return results, detailed_result, total_score
