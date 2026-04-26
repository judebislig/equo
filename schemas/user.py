# schemas/user.py
# Pydantic models that define shape of API requests and responses for users - turns data into Python object
# SQLAlchemy models (models/user.py) define the actual database table

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from core.enums import GoalType

# Shape of the incoming request body when creating a new user
class UserCreate(BaseModel):
    name: str
    age: int
    sex: str
    weight: float      
    height: float      
    goal: GoalType = GoalType.maintain  # bulk, cut, maintain. Default is maintain for now

# Shape of the incoming request body when updating an existing user
class UserUpdate(BaseModel):
    weight: Optional[float] = None
    height: Optional[float] = None
    goal: Optional[GoalType] = None
    age: Optional[int] = None
    calorie_target: Optional[float] = None

# Shape of the outgoing response body when returning user data
class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    sex: str
    weight: Optional[float] = None
    height: Optional[float] = None
    goal: GoalType
    calorie_target: float
    created_at: Optional[datetime] = None   # set automatically by database on insert

    class Config:
        from_attributes = True  # allows Pydantic to read SQLAlchemy model objects directly