# schemas/meal.py
# Pydantic models that define shape of API requests and responses for users - turns data into Python object
# SQLAlchemy models (models/user.py) define the actual database table

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Shape of the incoming request body when creating a new meal
class MealCreate(BaseModel):
    user_id: int
    meal_type: str
    description: str


# Shape of the incoming request body when updating an existing meal
class MealUpdate(BaseModel):
    weight: Optional[float] = None
    height: Optional[float] = None
    goal: Optional[GoalType] = None
    calorie_target: Optional[float] = None


# Shape of the outgoing response body when returning meal data
class MealResponse(BaseModel):
    id: int
    name: str
    age: int
    weight: Optional[float] = None
    height: Optional[float] = None
    calorie_target: float
    created_at: Optional[datetime] = None   # set automatically by database on insert

    class Config:
        from_attributes = True  # allows Pydantic to read SQLAlchemy model objects directly