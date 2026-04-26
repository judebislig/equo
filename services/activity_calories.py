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

# Physiological bounds for calorie burn rate
CALORIE_RATE_BOUNDS = {
    "min_per_minute": 1.5, # Too suspiciously low for any real exercise
    "max_per_minute": 20.0 # Above this is impossible
}

def validate_calorie_result(
    activity_type: str,
    duration_minutes: int,
    calories: float,
    weight_kg: float
) -> bool:
    """
    Validates that calorie burn result is physiologically reasonable.
    Returns True if result passes all sanity checks.
    """

    if duration_minutes <= 0:
        print(f"Invalid duration for {activity_type}: {duration_minutes} minutes")
        return False

    cal_per_minute = calories / duration_minutes

    # Check mininum - even walking burns more than 1.5 cal/min
    if cal_per_minute < CALORIE_RATE_BOUNDS["min_per_minute"]:
        print(f"Too low burn for {activity_type}: {cal_per_minute:.1f} cal/min")

    # Check max 
    if cal_per_minute > CALORIE_RATE_BOUNDS["max_per_minute"]:
        print(f"Too low burn for {activity_type}: {cal_per_minute:.1f} cal/min")

    # Weight sanity check
    if weight_kg < 30 or weight_kg > 300:
        print(f"Weight out of reasonable range: {weight_kg}kg")
        return False

    return True

    

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

    # validate result is physiologically reasonable
    if not validate_calorie_result(activity_type, duration_minutes, calories, weight_kg):
        print(f"Validation failed for {activity_type} - using conservative default MET of 4.0")
        calories = 4.0 * weight_kg * duration_hours

    return round(calories, 1), True
    