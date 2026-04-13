from enum import Enum

class GoalType(str, Enum):
    maintain = "maintain"
    cut = "cut"
    bulk = "bulk"