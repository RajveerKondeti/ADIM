from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str

class ProjectCreate(BaseModel):
    name: str
    description: str