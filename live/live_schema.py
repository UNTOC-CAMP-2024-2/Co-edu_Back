from pydantic import BaseModel

class Run(BaseModel):
    code : str
    language : str
    input : str