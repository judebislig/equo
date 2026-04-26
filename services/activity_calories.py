# services/calories.py
# Deterministic calorie burn calculation using MET formula
# Formula: calories = MET x weight_kg x (duration_minutes / 60)
# No LLM involved — pure math
# Called by routers/workouts.py when a workout is logged