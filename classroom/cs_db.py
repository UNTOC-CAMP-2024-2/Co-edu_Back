from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from variable import *


SQLALCHEMY_DATABASE_URL_CS = f"mysql+mysqlconnector://root:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{CS_DB_NAME}?charset=utf8mb4&collation=utf8mb4_unicode_ci"

cs_engine = create_engine(SQLALCHEMY_DATABASE_URL_CS, pool_recycle=3600,pool_pre_ping=True)

cs_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cs_engine)

cs_Base = declarative_base()

def get_csdb():
    db = cs_SessionLocal()
    try:
        yield db
    finally:
        db.close()