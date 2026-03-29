from pydantic import BaseModel, EmailStr
from typing import Optional


# -------- TASK SCHEMAS --------

class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    owner_id: int

    class Config:
        from_attributes = True


# -------- USER SCHEMAS --------

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str

    class Config:
        from_attributes = True


# -------- TOKEN --------

class Token(BaseModel):
    access_token: str
    token_type: str