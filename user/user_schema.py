from pydantic import BaseModel, EmailStr, field_validator
from fastapi import HTTPException

class NewUserForm(BaseModel):
    user_id : str
    password : str
    name : str
    email : EmailStr
    is_mentor : bool

    @field_validator('email','user_id','password','name')
    def check_empty(cls, v):
        if not v or v.isspace():
            raise HTTPException(status_code=422, detail="모든 항목을 입력해주세요.")
        return v
    
    @field_validator('password')
    def validate_password(cls,v):
        if len(v) < 8 or not any(char.isdigit() for char in v) or not any(char.isalpha() for char in v):
            raise HTTPException(status_code=422, detail="비밀번호는 8자리 이상, 영문과 숫자를 포함하여 입력해주세요.")
        return v
    
class LoginForm(BaseModel):
    user_id : str
    password : str
class EmailVerification(BaseModel):
    user_id : str
    email : str
    code : str

class Token(BaseModel):
    token : str

class TokenRefresh(BaseModel):
    reftoken : str