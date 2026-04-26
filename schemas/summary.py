# schemas/summary.py
# Pydantic response model for daily calorie summary
# Computed from meals and workouts logged today

from pydantic import BaseModel, computed_field
from typing import Optional, ClassVar
from datetime import date
from core.enums import GoalType, CUT_OFFSET, BULK_OFFSET

class DailySummaryResponse(BaseModel):
    user_id: int
    date: date
    goal: str               # bulk, cut, maintain

    # Biological data for on-the-fly TDEE
    weight_kg: float
    height_cm: float
    age: int
    sex: str

    # Aggregated totals from router
    calories_eaten: float   # From meals
    protein_eaten: float
    carbs_eaten: float
    fat_eaten: float
    calories_burned: float  # From workouts

    # Computed fields - calculated from the above
    @computed_field
    @property
    def base_tdee(self) -> float:
        """
        Mifflin-St Jeor BMR * Sedentary Factor (1.2)
        We intentionally use sedentary as the base because actual exercise calories 
        are added separately via calories_burned from logged workouts.
        """
        if self.sex.lower() == "male":
            bmr = (10 * self.weight_kg) + (6.25 * self.height_cm) - (5 * self.age) + 5
        else:
            bmr = (10 * self.weight_kg) + (6.25 * self.height_cm) - (5 * self.age) - 161
        return round(bmr * 1.2, 1)

    @computed_field
    @property
    def current_tdee(self) -> float:
        # Dynamic TDEE: Baseline + specific exercise
        return round(self.base_tdee + self.calories_burned, 1)

    @computed_field
    @property
    def calorie_target(self) -> float:
        # Target moves based on the dynamic TDEE
        # These offsets are defined in core.enums
        if self.goal.lower() == "cut":
            return round(self.current_tdee - CUT_OFFSET, 1)
        elif self.goal.lower() == "bulk":
            return round(self.current_tdee + BULK_OFFSET, 1)
        return self.current_tdee

    @computed_field
    @property
    def calories_vs_target(self) -> float:
        """
        The gap between current intake and the goal target.
        Positive = Under target (Eat more)
        Negative = Over target (Exceeded goal)
        """
        return round(self.calorie_target - self.calories_eaten, 1)
    
    @computed_field
    @property
    def weekly_forecast_kg(self) -> float:
        net_daily_balance = self.calories_eaten - self.current_tdee
        return round((net_daily_balance * 7) / 7700, 2)

    @computed_field
    @property
    def goal_status(self) -> str:
        diff = self.calories_vs_target
        vs_tdee = self.calories_eaten - self.current_tdee
        goal = self.goal.lower()

        if goal == "cut":
            if diff >= 0: return "On track - under cut target"
            if vs_tdee < 0: return "Over target but still in a deficit"
            return "Over maintenance - no deficit today"
        
        if goal == "bulk":
            if diff <= 0: return "On track - hitting your surplus"
            if vs_tdee > 0: return "Under target but still in a surplus"
            return "Under maintenance - eat more to grow"
            
        if goal == "maintain":
            if abs(vs_tdee) <= 100:
                return "On track - close to maintenance"
            elif vs_tdee < 0:
                return f"Under maintenance by {abs(vs_tdee):.0f} calories"
            else:
                return f"Over maintenance by {vs_tdee:.0f} calories"
        
        return "on track"
        
        
    class Config:
        from_attributes = True