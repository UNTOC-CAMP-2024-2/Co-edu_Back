from sqlalchemy.orm import Session
from assignment.assign_model import *


#랜덤코드 발급시 중복확인
def check_id(id, db: Session):
    data = db.query(Assignment).filter(Assignment.assignment_id == id).first()
    if data:
        return None
    else:
        return id
    

def add_testcase(db: Session, assignment_id: str, input_data: str, expected_output: str):
    # Get the current highest case_number for the given assignment_id
    max_case_number = (db.query(AssignmentTestcase.case_number)
                        .filter(AssignmentTestcase.assignment_id == assignment_id)
                        .order_by(AssignmentTestcase.case_number.desc())
                        .first())
    new_case_number = (max_case_number[0] + 1) if max_case_number else 1

    new_testcase = AssignmentTestcase(
        assignment_id=assignment_id,
        case_number=new_case_number,
        input=input_data,
        expected_output=expected_output
    )
    db.add(new_testcase)
    db.commit()
    db.refresh(new_testcase)
    return new_case_number

def delete_testcase(db: Session, assignment_id: int, case_number: int):
    # Delete the specified testcase
    db.query(AssignmentTestcase)\
      .filter(AssignmentTestcase.assignment_id == assignment_id, AssignmentTestcase.case_number == case_number)\
      .delete()
    db.commit()

    # Reorder the remaining cases for the assignment_id
    testcases = db.query(AssignmentTestcase)\
                  .filter(AssignmentTestcase.assignment_id == assignment_id)\
                  .order_by(AssignmentTestcase.case_number.asc())\
                  .all()

    for index, testcase in enumerate(testcases, start=1):
        testcase.case_number = index
    db.commit()


def delete_assignment(db: Session, assignment):

    db.query(AssignmentTestcase).filter(
        AssignmentTestcase.assignment_id == assignment.assignment_id
    ).delete(synchronize_session=False)

    db.query(AssignmentFeedBack).filter(
        AssignmentFeedBack.assignment_id == assignment.assignment_id
    ).delete(synchronize_session=False)
    
    db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment.assignment_id
    ).delete(synchronize_session=False)
    db.delete(assignment)
    db.commit()
