import os
from dotenv import load_dotenv



load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", 3306)
USER_DB_NAME = os.environ.get("USER_DB_NAME")
CS_DB_NAME = os.environ.get("CS_DB_NAME")
AS_DB_NAME = os.environ.get("AS_DB_NAME")

EMAIL = os.environ.get("EMAILADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAILPASSWORD")

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS"))