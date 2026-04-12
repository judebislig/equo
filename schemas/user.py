# schemas/user.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    age: int
    weight: Optional[float] = None
    height: Optional[float] = None
    goal: str   # bulk, cut, maintain
    calorie_target: float

class UserUpdate(BaseModel):
    weight: Optional[float] = None
    height: Optional[float] = None
    goal: Optional[str] = None
    calorie_target: Optional[float] = None

class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    weight: Optional[float] = None
    height: Optional[float] = None
    goal: str
    calorie_target: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True