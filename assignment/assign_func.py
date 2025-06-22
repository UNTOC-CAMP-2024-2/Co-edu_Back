from sqlalchemy.orm import Session
from assignment.assign_model import *
from fastapi import HTTPException
from datetime import datetime

def returnnow():
    date = str(datetime.now().date())
    date = date.replace('-','. ')+". "
    return date
#랜덤코드 발급시 중복확인
def check_id(id, db: Session):
    data = db.query(Assignment).filter(Assignment.assignment_id == id).first()
    if data:
        return None
    else:
        return id
    
def is_assignment_created(id, assignment_id, db: Session):
    data = db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()
    if data == None :
        return HTTPException(status_code=404, detail="과제가 존재하지 않습니다.")
    if data.created_by == id :
        return id
    else :
        return HTTPException(status_code=409, detail="과제 생성자가 아닙니다.")

def create_testcase(tc_list, asid , db:Session):
    for testcase in tc_list :
        new_testcase = AssignmentTestcase(assignment_id = asid, input = testcase.input_data, expected_output = testcase.expected_output)
        db.add(new_testcase)
    db.commit()

def delete_testcase(db: Session, assignment_id: int):
    # Delete the specified testcase
    db.query(AssignmentTestcase)\
      .filter(AssignmentTestcase.assignment_id == assignment_id).delete()
    db.commit()

def modify_testcase(tc_list, asid, db:Session):
    delete_testcase(db,asid)
    create_testcase(tc_list,asid,db)

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

def create_new_category(data,as_db:Session):

    existing = as_db.query(AssignmentCategory).filter_by(name=data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="같은 이름의 카테고리가 이미 존재합니다.")
    
    new_category = AssignmentCategory(
        name=data.name,
        description=data.description,
        class_id = data.class_id
    )
    as_db.add(new_category)
    as_db.commit()
    as_db.refresh(new_category)

    return {
        "message": "카테고리가 성공적으로 생성되었습니다.",
        "category": {
            "id": new_category.id,
            "class_id": new_category.class_id,
            "name": new_category.name,
            "description": new_category.description
        }
    }