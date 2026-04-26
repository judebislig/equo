# services/calories.py
# Deterministic calorie burn calculation using MET formula
# Formula: calories = MET x weight_kg x (duration_minutes / 60)
# No LLM involved — pure math
# Called by routers/workouts.py when a workout is logged

from core.enums import ActivityType

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
    return [0, False]