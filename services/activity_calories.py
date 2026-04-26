# services/calories.py
# Deterministic calorie burn calculation using MET formula
# Formula: calories = MET x weight_kg x (duration_minutes / 60)
# No LLM involved — pure math
# Called by routers/workouts.py when a workout is logged

from core.enums import ACTIVITY_MET_MAP

# ==========================================
# 1. MET DATABASE
# ==========================================

# ==========================================
# 2. VALIDATION
# ==========================================

def calculate_calories_burned(
    activity_type: str,
    duration_minutes: int,
    weight_kg: float,
    calories_override: float = None
) -> tuple[float, bool]:
    """
    Calculate calories burned for a workout.
    Returns (calories_burned, is_estimated) where is_estimated is false when override is used and true when MET formula is used
    """

    if calories_override is not None and calories_override > 0:
        return round(calories_override, 1), False
    
    # Look up MET directly from the map
    met = ACTIVITY_MET_MAP.get(activity_type.lower(), 5.0) # Default MET to 5
    duration_hours = duration_minutes / 60
    calories = met * weight_kg * duration_hours

    return round(calories, 1), True
    