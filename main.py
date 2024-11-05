from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from user.user_router import router as user_router
from user.user_db import user_Base,user_engine
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.environ.get("EMAILADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAILPASSWORD")
smtp = smtplib.SMTP('smtp.gmail.com', 587)

smtp.ehlo()

smtp.starttls()

#로그인을 통해 지메일 접속
smtp.login(EMAIL, EMAIL_PASSWORD)

app = FastAPI()
user_Base.metadata.create_all(bind=user_engine)
app.include_router(user_router, tags=["user"])

@app.get("/")
async def init():
    return {"init"}

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn

    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
