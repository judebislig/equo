# services/nutrition.py
# Handles all food parsing and nutrition lookup logic
# Flow: natural language -> Gemini extracts items -> USDA looks up nutrition / LLM fallback -> return
# Caching can be added later as an optimization

import httpx
import json
import os
from core.food_logic import get_portion_in_grams, calculate_relevance_score
from services.prompts import nlp_extract_ingredients_PROMPT, LLM_FALLBACK_PROMPT
from google import genai

# Load environment variables for API keys
USDA_API_KEY = os.getenv("USDA_API_KEY")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-flash-latest"

# ==========================================
# 1. UTILITIES & JSON HELPERS
# ==========================================

def parse_json_from_text(text: str) -> dict:
    """
    Helper function to extract JSON from Gemini response text
    """
    decoder = json.JSONDecoder()

    for i, char in enumerate(text):
        if char == "{":
            try:
                obj, _ = decoder.raw_decode(text[i:])
                return obj
            except json.JSONDecodeError:
                continue

    raise ValueError("No JSON object found in the text")

# ==========================================
# 2. DATA MAPPERS
# ==========================================

def map_usda_to_macros(food_data: dict) -> dict:
    """
    Extracts calories, protein, carbs, and fat from USDA food data
    Returns a dict with these values, defaulting to 0 if not found
    """
    nutrients = {}
    for n in food_data.get("foodNutrients", []):
        name = n.get("nutrientName", "").lower()
        value = n.get("value", 0)
        nutrients[name] = value

    # USDA uses different keys for calories, so we check multiple possibilities
    calories = nutrients.get("energy (kcal)") or nutrients.get("energy", 0)

    return {
        "calories": calories,
        "protein": nutrients.get("protein", 0),
        "carbs": nutrients.get("carbohydrate, by difference", 0),
        "fat": nutrients.get("total lipid (fat)", 0)
    }

# ==========================================
# 3. EXTERNAL CLIENTS (USDA & GEMINI)
# ==========================================

def nlp_extract_ingredients(description: str) -> list[dict]:
    """
    Main function to extract food items from a meal description
    Returns a list of dicts with "item" and "amount" keys, e.g., [{"item": "chicken breast", "amount": "150g"}, ...]
    """
    prompt = nlp_extract_ingredients_PROMPT.format(description=description)
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    data = parse_json_from_text(response.text)
    items = data.get("items", [])

    if isinstance(items, dict):
        items = [items]  # ensure it's always a list

    return items

def llm_fallback(food_name: str, amount: str) -> dict:
    """
    LLM fallback to estimate nutrition for a food item when USDA lookup fails
    Returns a dict with estimated nutrition info based on the LLM prompt
    """
    response = client.models.generate_content(
        model=MODEL,
        contents=LLM_FALLBACK_PROMPT.format(amount=amount, food_name=food_name)
    )
    print(f"LLM fallback response for {food_name}: {response.text}")
    result = parse_json_from_text(response.text)
    result["estimated"] = True  # mark this as an estimate
    return result

def call_usda_api(food_name: str, amount_str: str) -> dict | None:
    """
    Function to look up nutrition info for a given food item using USDA API
    Implements relevance scoring to find the best match and scales nutrition based on portion size
    Returns a dict with standardized nutrition info or None if no good match is found
    """
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "query": food_name,
        "api_key": USDA_API_KEY,
        "pageSize": 10,
        "dataType": "SR Legacy,Foundation,Survey (FNDDS)" 
    }
    try:
        response = httpx.get(url, params=params)
        results = response.json().get("foods", [])
        
        if not results:
            print(f"No USDA data found for {food_name}")
            return None
        
        # 1. Rank results using our relevance scoring function
        # food_name is the user's query, f is the USDA food item dict, and we calculate a score for how well it matches
        scored_results = []
        for f in results:
            score = calculate_relevance_score(food_name, f)
            scored_results.append((score, f))

        scored_results.sort(key=lambda x: x[0], reverse=True)  # sort by score descending
        best_score, best_match = scored_results[0]

        # 2. Safety check: if even the best match is poor, go to LLM fallback
        if best_score < 45:  # arbitrary threshold for relevance
            print(f"USDA data for '{food_name}' is not relevant enough (score: {best_score}), skipping to LLM fallback")
            return None
        
        # 3. Scale macros based on portion
        base_macros = map_usda_to_macros(best_match)
        gram_weight = get_portion_in_grams(food_name, amount_str)

        # USDA data is per 100g, so calculate scaling factor
        multiplier = gram_weight / 100.0

        # Return standardized nutrition info - calories, protein, carbs, fat
        return {
            "food_name": best_match["description"],
            "calories": round(base_macros["calories"] * multiplier, 2),
            "protein": round(base_macros["protein"] * multiplier, 2),
            "carbs": round(base_macros["carbs"] * multiplier, 2),
            "fat": round(base_macros["fat"] * multiplier, 2),
            "estimated": False  # indicates this is an exact USDA data
        }
    except Exception as e:
        print(f"USDA API error for '{food_name}': {e}")
        return None

# ==========================================
# 4. COORDINATORS (The "Middle Managers")
# ==========================================

def get_nutrition(food_name: str, amount: str) -> dict:
    """
    Main function to get nutrition info for a food item and amount
    Tries USDA lookup first, then falls back to LLM estimation if necessary
    Returns a dict with nutrition info (calories, protein, carbs, fat) and whether it was estimated
    """
    nutrition = call_usda_api(food_name, amount)
    if nutrition:
        print(f"USDA match: {nutrition['food_name']}")
        return nutrition
    else:
        print(f"Using LLM fallback for {food_name}")
        return llm_fallback(food_name, amount)

# ==========================================
# 5. THE MAIN PIPELINE
# ==========================================

def parse_meal(description: str) -> dict:
    """
    Full meal parsing pipeline:
    1. Extract food items from natural language description using Gemini
    2. Look up each item in USDA database using relevance scoring to find best match
    3. If USDA lookup fails or the best match is poor, use LLM fallback to estimate nutrition
    4. Sum total calories, protein, carbs, and fat for the meal

    Input example: "chicken breast with rice and broccoli"
    Output example: {"food_name": "chicken breast, rice, broccoli", "calories": 600, "protein": 50, "carbs": 60, "fat": 10, "has_estimates": False}
    """
    # Step 1: Extract food items and amounts using Gemini
    food_items = nlp_extract_ingredients(description)
    print(f"Extracted food items: {food_items}")

    # Step 2 & 3: Get nutrition for each item, using USDA or LLM fallback
    total = {"food_names": [], "calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "has_estimates": False}

    for item in food_items:
        # Get nutrition info for this item and amount, including food name, calories, protein, carbs, fat, and whether it was an estimate
        nutrition = get_nutrition(item["item"], item["amount"])

        # Keep track of food names and sum up macros for the whole meal
        total["food_names"].append(nutrition["food_name"])
        total["calories"] += nutrition["calories"]
        total["protein"] += nutrition["protein"]
        total["carbs"] += nutrition["carbs"]
        total["fat"] += nutrition["fat"]

        # If any item was estimated, mark the whole meal as having estimates
        if nutrition.get("estimated"):
            total["has_estimates"] = True

    return {
        "food_name": ", ".join(total["food_names"]),
        "calories": total["calories"],
        "protein": total["protein"],
        "carbs": total["carbs"],
        "fat": total["fat"],
        "has_estimates": total["has_estimates"]
    }