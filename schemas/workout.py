# schemas/workout.py
# Pydantic models that define shape of API requests and responses for workouts - turns data into Python object
# SQLAlchemy models (models/workout.py) define the actual database table

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Shape of the incoming request body when creating a new workout
class WorkoutCreate(BaseModel):
    user_id: int
    activity_type: str
    duration_minutes: int = Field(gt=0)
    calories_override: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=500)

# Shape of the outgoing response body when returning workout data
class WorkoutResponse(BaseModel):
    id: int
    user_id: int
    activity_type: str
    duration_minutes: int
    calories_burned: float
    is_estimated: bool = True
    notes: Optional[str] = None
    logged_at: Optional[datetime] = None  

    class Config:
        from_attributes = True  # allows Pydantic to read SQLAlchemy model objects directly

