# schemas/meal.py
# Pydantic models that define shape of API requests and responses for meals - turns data into Python object
# SQLAlchemy models (models/meal.py) define the actual database table

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from core.enums import MealType

# Shape of the incoming request body when creating a new meal
class MealCreate(BaseModel):
    user_id: int
    meal_type: MealType
    description: str

# Shape of the outgoing response body when returning meal data
class MealResponse(BaseModel):
    id: int
    user_id: int
    meal_type: MealType
    description: str    # original imput
    food_name: str      # Gemini parsed
    calories: float     # Gemini estimated
    protein: float      # Gemini estimated
    carbs: float        # Gemini estimated
    fat: float          # Gemini estimated
    is_estimated: bool = False
    logged_at: Optional[datetime] = None  

    class Config:
        from_attributes = True  # allows Pydantic to read SQLAlchemy model objects directly