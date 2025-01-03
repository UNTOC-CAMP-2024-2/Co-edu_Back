from fastapi import APIRouter, HTTPException, Depends,Security, status,BackgroundTasks
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
                  ,cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else:
        check_created(user,assignment.class_id,cs_db)
        is_assignment_created(user,as_db) #권한쟁의
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


@router.get("/status/maker") #
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
        is_assignment_created(user,as_db)
        
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


@router.post("/testcase") 
def testcase(data : TestCase,credentials: HTTPAuthorizationCredentials = Security(security),
             as_db : Session=Depends(get_asdb),
             cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
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
             cs_db : Session=Depends(get_csdb)):
    token = credentials.credentials
    user = token_decode(token)
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).first()
    check_created(user,assignment.class_id,cs_db)
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
                                      , submitted_at = datetime.utcnow(),code = data.code
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
    assignment = as_db.query(Assignment).filter(Assignment.assignment_id == data.assignment_id).all()
    if assignment == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    else :
        check_created(user,assignment.class_id,cs_db)
        is_assignment_created(user,as_db)
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
        submitted_at=datetime.utcnow(),
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
