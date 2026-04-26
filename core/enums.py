from enum import Enum

# ==========================================
# ACTIVITY TYPES WITH MET VALUES
# ==========================================

# MET values from Compendium of Physical Activities (Ainsworth et al.)
# Grouped by category for readability
# Format: "activity_name": met_value

ACTIVITY_MET_MAP = {
    # Cardio
    "running": 9.8,
    "jogging": 7.0,
    "walking": 3.5,
    "hiking": 6.0,
    "cycling": 7.5,
    "swimming": 8.0,
    "rowing": 8.5,
    "elliptical": 5.0,
    "jump rope": 12.3,
    "stair climbing": 9.0,

    # Strength
    "weightlifting": 5.0,
    "bodyweight": 3.8,
    "crossfit": 8.0,
    "powerlifting": 6.0,

    # Classes
    "hiit": 10.0,
    "yoga": 2.5,
    "pilates": 3.0,
    "stretching": 2.3,

    # Sports
    "boxing": 9.8,
    "basketball": 8.0,
    "soccer": 10.0,
    "tennis": 7.3,
    "volleyball": 4.0,
    "golf": 3.5,
    "dance": 5.0,
    "martial arts": 10.0,
    "rock climbing": 8.0,
    "pickleball": 5.0
}

# ActivityType enum is auto-generated from ACTIVITY_MET_MAP keys
# Adding a new activity only requires adding it to ACTIVITY_MET_MAP above
ActivityType = Enum(
    "ActivityType",
    {name.upper().replace(" ", "_"): name for name in ACTIVITY_MET_MAP.keys()},
    type=str
)

# ==========================================
# 2. VALIDATION
# ==========================================

class GoalType(str, Enum):
    maintain = "maintain"
    cut = "cut"
    bulk = "bulk"

class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"

class SexType(str, Enum):
    male = "male"
    female = "female"

# Define standard offsets as constants
CUT_OFFSET= 500
BULK_OFFSET = 300    