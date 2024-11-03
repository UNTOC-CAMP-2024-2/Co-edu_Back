from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from user import user_router

app = FastAPI()
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
