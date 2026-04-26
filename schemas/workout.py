# schemas/workout.py
# Pydantic models that define shape of API requests and responses for workouts - turns data into Python object
# SQLAlchemy models (models/workout.py) define the actual database table

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from core.enums import ACTIVITY_MET_MAP

# Shape of the incoming request body when creating a new workout
class WorkoutCreate(BaseModel):
    user_id: int
    activity_type: str
    duration_minutes: int = Field(gt=0)
    calories_override: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=500)

    @validator("activity_type")
    def activity_must_be_valid(cls, v):
        if v.lower() not in ACTIVITY_MET_MAP:
            raise ValueError(f"activity_type must be one of: {', '.join(ACTIVITY_MET_MAP.keys())}")
        return v.lower()

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

