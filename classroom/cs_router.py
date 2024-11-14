from fastapi import APIRouter, HTTPException, Depends,Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
<<<<<<< Updated upstream
from user.user_db import get_userdb
from user.user_model import User,VerifiedEmail
from user.user_func import *
from user.user_schema import *
import random
import datetime
=======

from classroom.cs_model import Classroom,UserToClass
from classroom.cs_schema import NewClassroom
from classroom.cs_func import *
from classroom.cs_db import get_csdb

from user.user_func import *
from user.user_db import get_userdb

import random
>>>>>>> Stashed changes

security = HTTPBearer()


router = APIRouter(
    prefix="/classroom",
<<<<<<< Updated upstream
)
=======
)

@router.post("/create")
async def create_classroom(data: NewClassroom,credentials: HTTPAuthorizationCredentials = Security(security),cs_db : Session=Depends(get_csdb), user_db : Session=Depends(get_userdb)):
    token = credentials.credentials
    user = token_decode(token)
    check_mentor(user, user_db)
    new_code = str(random.randint(10000,99999))
    while new_code != None:
        new_code = str(random.randint(10000,99999))
        new_code = check_code(new_code,cs_db)

    cs_data = Classroom(class_name = data.class_name, code = new_code, description = data.description,
                     max_member = data.max_mameber,created_by = user)
    usercs_data = UserToClass(user_id = user, class_code = new_code)
    
    cs_db.add(cs_data)
    cs_db.add(usercs_data)
    cs_db.commit()
    cs_db.refresh(cs_data)
    cs_db.refresh(usercs_data)
    return {"class_name" : data.class_name, "code": new_code, "created_by" : user}
>>>>>>> Stashed changes
