# schemas/summary.py
# Pydantic response model for daily calorie summary
# Computed from meals and workouts logged today

from pydantic import BaseModel, computed_field
from typing import Optional
from datetime import date
from core.enums import GoalType

class DailySummaryResponse(BaseModel):
    user_id: int
    date: date
    calorie_target: float
    goal: str   # bulk, cut, maintain

    # Meals
    calories_eaten: float
    protein_eaten: float
    carbs_eaten: float
    fat_eaten: float

    # Workouts
    calories_burned: float

    # Computed fields - calculated from the above
    @computed_field
    @property
    def net_calories(self) -> float:
        return round(self.calories_eaten - self.calories_burned, 1)
    
    @computed_field
    @property
    def calories_remaining(self) -> float:
        return round(self.calorie_target - self.net_calories, 1)
    
    @computed_field
    @property
    def goal_status(self) -> str:
        diff = self.calories_remaining
        goal = self.goal.lower()

        if abs(diff) <= 100: # within 100 calories of goal
            return "on track"
        
        if goal == "bulk":
            if diff > 100:
                return "under target - eat more to hit your surplus"
            else:
                return "over target - you've exceeded your surplus"
            
        elif goal == "cut":
            if diff > 100:
                return "under target - you're in a good deficit"
            else:
                return "over target - you've exceeded your calorie limits"
            
        elif goal == "maintain":
            if diff > 100:
                return "under target - eat a bit more to maintain"
            else:
                return "over target - slightly over your maintenance calories"
            
        return "on track"
        
        
    class Config:
        from_attributes = True