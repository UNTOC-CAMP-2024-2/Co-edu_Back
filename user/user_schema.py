from pydantic import BaseModel, EmailStr, field_validator
from fastapi import HTTPException

class NewUserForm(BaseModel):
    user_id : str
    password : str
    name : str
    nickname : str
    email : EmailStr

    @field_validator('email','user_id','password','name','nickname')
    def check_empty(cls, v):
        if not v or v.isspace():
            raise HTTPException(status_code=422, detail="모든 항목을 입력해주세요.")
        return v
    
