from enum import Enum

class GoalType(str, Enum):
    maintain = "maintain"
    cut = "cut"
    bulk = "bulk"

class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"