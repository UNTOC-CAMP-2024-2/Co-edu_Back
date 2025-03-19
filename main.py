from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from user.user_router import router as user_router
from user.user_db import user_Base,user_engine

from classroom.cs_router import router as cs_router
from classroom.cs_db import cs_Base,cs_engine

from assignment.assign_router import router as as_router
from assignment.assign_db import as_Base,as_engine

from live.live_router import router as live_router
from variable import *
import logging
import logging.config
from log_config import LOGGING_CONFIG  

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("fastapi")

app = FastAPI()
user_Base.metadata.create_all(bind=user_engine)
cs_Base.metadata.create_all(bind=cs_engine)
as_Base.metadata.create_all(bind=as_engine)
app.include_router(user_router, tags=["user"],)
app.include_router(cs_router, tags=["classroom"])
app.include_router(as_router, tags=["assignment"])
app.include_router(live_router, tags=["live_classroom"])


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
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=7777,
        reload=True,
        ssl_certfile=SSL_CERTFILE,  
        ssl_keyfile=SSL_KEYFILE,    
    )