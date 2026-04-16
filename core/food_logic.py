# core/food_logic.py
# Contains core logic for getting portion sizes and scoring USDA results based on relevance to the user's query
# This is where we implement the heuristics for interpreting portion sizes and ranking USDA results

import re
from thefuzz import fuzz

RED_FLAGS = ["spread", "beverage", "liquid", "baby food", "infant", "juice", "drink", "flavor", "sauce", "powder", "mix"]
PREMIUM_DATA_TYPES = ["SR Legacy", "Foundation"]  # prioritize these data types in USDA results

# Helper function to convert portion descriptions into grams for scaling USDA nutrition data (e.g., "2 slices of bread" -> 60g)
def get_portion_in_grams(amount_str: str, food_item: str) -> float:
    # Standardize input
    amount_str = str(amount_str).lower().strip()

    # Extract number and unit using regex
    match = re.search(r"([0-9.]+)\s*([a-zA-Z]*)", amount_str)
    if not match:
        return 100.0  # default to 100g if we can't parse the amount
    
    value = float(match.group(1))
    unit = match.group(2)

    # Conversion mapping (standard weights in grams)
    conversions = {
        "oz": 28.35,
        "ounce": 28.35,
        "lb": 453.59,
        "cup": 240.0,
        "tbsp": 15.0,
        "tsp": 5.0,
        "g": 1.0,
        "gram": 1.0,
        "slice": 30.0, # Average bread slice
        "small": 100.0,
        "medium": 150.0,
        "large": 250.0
    }

    # Heuristic for unitless portions (like '0.5' for a tortilla)
    if not unit or unit == "portion":
        if any(keyword in food_item.lower() for keyword in ["bread", "tortilla", "wrap", "bun", "bagel"]):
            return value * 80.0  # assume 80g per portion for bread-like items
        return value * 100.0  # default portion size in grams
    
    return value * conversions.get(unit, 100.0)  # default to 100g if unit is unrecognized

# Ranks USDA results based on string similarity and presence of red flags
def calculate_relevance_score(query: str, fdc_item: dict) -> float:
    description = fdc_item.get("description", "").lower()
    query = query.lower()

    # 1. Base score on fuzzy string matching
    score = fuzz.token_sort_ratio(query, description)

    # 2. Penalize if any red flag words are present in the description
    for flag in RED_FLAGS:
        if flag in description and flag not in query:
            score -= 50  # arbitrary penalty for red flags

    # 3. Bonus: Reliable data sources (Foundation foods are better than branded)
    if fdc_item.get("dataType") in PREMIUM_DATA_TYPES:
        score += 20  # arbitrary bonus for premium data types

    return score