# core/food_logic.py
# Contains core logic for getting portion sizes and scoring USDA results based on relevance to the user's query
# This is where we implement the heuristics for interpreting portion sizes and ranking USDA results

import re
from thefuzz import fuzz

# ==========================================
# 1. HEURISTIC CONFIGURATIONS
# ==========================================

# Volume to weight (portion logic)
DENSITY_MAP = {
    "cup": [
        (["spinach", "kale", "lettuce", "broccoli", "cucumber", "cabbage"], 30.0),  # leafy greens
        (["pasta", "cereal", "dry"], 100.0),  # dry bulky items
        (["rice", "flour", "sugar"], 150.0),  # cooked rice/grains are denser
        ([], 240.0)  # default cup weight
    ],
    "portion": [
        (["bread", "tortilla", "wrap", "bun", "bagel"], 80.0),  # bread-like items
        (["egg"], 50.0),  # average large egg
        ([], 100.0)  # default portion size in grams
    ]
}

# Weight to calories (sanity logic) per 100g - these are upper bounds for sanity checks based on typical calorie densities of different food categories
CALORIE_DENSITY_MAP = {
    "leafy_greens": (["spinach", "kale", "lettuce", "broccoli", "cucumber", "cabbage"], 120), 
    "starch_cooked": (["pasta", "rice", "quinoa", "potato", "oatmeal"], 200), 
    "protein_lean": (["chicken breast", "turkey breast", "white fish"], 250),  
    "eggs": (["egg"], 250)  
}

# USDA search ranking filters
RED_FLAGS = ["spread", "beverage", "liquid", "baby food", "infant", "juice", 
    "drink", "flavor", "sauce", "powder", "mix", "cracker", "cake",
    "roll", "deli", "patty", "nugget"]
PREMIUM_DATA_TYPES = ["SR Legacy", "Foundation"]  # prioritize these data types in USDA results

# ==========================================
# 2. CORE LOGIC FUNCTIONS
# ==========================================

def get_portion_in_grams(food_item: str, amount_str: str) -> float:
    """
    Converts a portion description into grams using heuristics and standard conversions
    If the amount is unparseable, defaults to 100g
    Returns a float representing the estimated weight in grams for the given portion description
    """
    # Standardize input
    amount_str = str(amount_str).lower().strip()

    # Extract number and unit using regex
    match = re.search(r"([0-9.]+)\s*([a-zA-Z]*)", amount_str)
    if not match:
        return 100.0  # default to 100g if we can't parse the amount
    
    value = float(match.group(1))
    unit = match.group(2).rstrip("s")  # remove plural 's' for standardization

    # Handle cup logic separately based on density
    if unit in ["cup", "cups"]:
        if any(x in food_item.lower() for x in ["spinach", "kale", "lettuce", "broccoli", "cucumber", "cabbage"]):
            unit_weight = 30.0  # 1 cup of leafy greens is about 30g
        elif any(x in food_item.lower() for x in ["pasta", "cereal", "dry"]):
            unit_weight = 100.0  # dry bulky items
        elif any(x in food_item.lower() for x in ["rice", "flour", "sugar"]):
            unit_weight = 150.0  # cooked rice/grains are denser
        else:
            unit_weight = 240.0  # default cup weight

    # Conversion mapping (standard weights in grams)
    conversions = {
        "oz": 28.35,
        "ounce": 28.35,
        "lb": 453.59,
        "tbsp": 15.0,
        "tsp": 5.0,
        "g": 1.0,
        "gram": 1.0,
        "slice": 30.0, # Average bread slice
        "small": 100.0,
        "medium": 150.0,
        "large": 250.0
    }

    if unit == "large":
        if any(x in food_item.lower() for x in ["shake", "soft drink", "soda", "juice", "drink", "slushie", "smoothie"]):
            return value * 500.0  # large beverage ~500g

    # Heuristic for unitless portions (like '0.5' for a tortilla)
    if not unit or unit == "portion":
        if any(keyword in food_item.lower() for keyword in ["bread", "tortilla", "wrap", "bun", "bagel"]):
            return value * 80.0  # assume 80g per portion for bread-like items
        return value * 100.0  # default portion size in grams
    return value * conversions.get(unit, 100.0)  # default to 100g if unit is unrecognized

def calculate_relevance_score(user_query: str, fdc_item: dict) -> float:
    """
    Calculates a relevance score for a USDA food item based on the user's query
    Higher score means more relevant. Uses fuzzy string matching and penalizes items with red flag words.
    """
    usda_description = fdc_item.get("description", "").lower()
    user_query = user_query.lower()

    # 1. Base score on fuzzy string matching - how closely does the USDA description (name)match the user's query?
    # Fuzz score will be between 0 and 100, where 100 is an exact match
    score = fuzz.token_sort_ratio(user_query, usda_description)

    # 2. Penalize if any red flag words are present in the description
    for flag in RED_FLAGS:
        if flag in usda_description and flag not in user_query:
            score -= 50  # arbitrary penalty for red flags

    # 3. Bonus: Reliable data sources (Foundation foods are better than branded)
    if fdc_item.get("dataType") in PREMIUM_DATA_TYPES:
        score += 20  # arbitrary bonus for premium data types

    return score

def validate_macro_logic(macros: dict) -> bool:
    """
    Uses the Atwater System to validate that the calories reported for a food item are consistent with its macronutrient breakdown
    Returns True if the calories are within a reasonable range of the calculated value, False otherwise
    """
    reported_calories = macros["calories_per_100g"]
    if reported_calories <= 0:
        return False
    
    # Atwater factors
    FAT_KCAL = 9
    PROTEIN_KCAL = 4
    CARB_KCAL = 4

    calculated_cals = (
        (macros.get("fat_per_100g", 0) * FAT_KCAL) +
        (macros.get("protein_per_100g", 0) * PROTEIN_KCAL) +
        (macros.get("carbs_per_100g", 0) * CARB_KCAL)
    )

    # Allow for a 20% margin of error in the calorie count
    discrepancy = abs(calculated_cals - reported_calories)
    margin = reported_calories * 0.20

    if discrepancy > margin:
        return False
    
    return True
