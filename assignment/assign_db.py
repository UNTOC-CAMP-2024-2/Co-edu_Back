from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from variable import *


SQLALCHEMY_DATABASE_URL_AS = f"mysql+mysqlconnector://root:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{AS_DB_NAME}?charset=utf8mb4&collation=utf8mb4_unicode_ci"

as_engine = create_engine(SQLALCHEMY_DATABASE_URL_AS)

as_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=as_engine)

as_Base = declarative_base()

def get_asdb():
    db = as_SessionLocal()
    try:
        yield db
    finally:
        db.close()