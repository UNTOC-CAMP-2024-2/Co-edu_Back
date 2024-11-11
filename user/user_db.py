from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", 3306)
USER_DB_NAME = os.environ.get("USER_DB_NAME")

SQLALCHEMY_DATABASE_URL_USER = f"mysql+mysqlconnector://root:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{USER_DB_NAME}?charset=utf8mb4&collation=utf8mb4_unicode_ci"

user_engine = create_engine(SQLALCHEMY_DATABASE_URL_USER)

user_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=user_engine)

user_Base = declarative_base()

def get_userdb():
    db = user_SessionLocal()
    try:
        yield db
    finally:
        db.close()