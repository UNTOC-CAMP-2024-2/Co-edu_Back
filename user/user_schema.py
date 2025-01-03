from pydantic import BaseModel, EmailStr

class NewUserForm(BaseModel):
    user_id : str
    password : str
    name : str
    email : EmailStr
    is_mentor : bool
    
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