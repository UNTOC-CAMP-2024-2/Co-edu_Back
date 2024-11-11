import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", 3306)
USER_DB_NAME = os.environ.get("USER_DB_NAME")
EMAIL = os.environ.get("EMAILADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAILPASSWORD")