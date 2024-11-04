from sqlalchemy.orm import Session
from user_model import User
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


#사용자 정보 여부 확인
def get_user(user_id: str, db: Session):
    return db.query(User).filter(User.user_id == user_id).first()
def get_user_nickname(nickname: str, db: Session):
    return db.query(User).filter(User.nickname == nickname).first()
def get_email(email: str, db: Session):
    return db.query(User).filter(User.email == email).first()

#패스워드 생성 및 확인
def get_password_hash(password):
    return pwd_context.hash(password)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)