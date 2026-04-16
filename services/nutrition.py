# services/nutrition.py
# Handles all food parsing and nutrition lookup logic
# Flow: natural language -> Gemini extracts items -> USDA looks up nutrition / LLM fallback -> return
# Caching can be added later as an optimization

import httpx
import json
import os
import re
from thefuzz import fuzz
from google import genai

# Constants for scoring USDA results
RED_FLAGS = ["spread", "beverage", "liquid", "baby food", "infant", "juice", "drink", "flavor", "sauce", "powder", "mix"]
PREMIUM_DATA_TYPES = ["SR Legacy", "Foundation"]  # prioritize these data types in USDA results
USDA_API_KEY = os.getenv("USDA_API_KEY")

# Initialize Gemini client with API key from environment variable
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-flash-latest"

# Helper function to extract JSON from Gemini response text
def extract_json(text: str) -> dict:
    decoder = json.JSONDecoder()

    for i, char in enumerate(text):
        if char == "{":
            try:
                obj, _ = decoder.raw_decode(text[i:])
                return obj
            except json.JSONDecodeError:
                continue

    raise ValueError("No JSON object found in the text")

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

# Safely pulls macros from the USDA's complex nutrient list
def extract_macros(food_data: dict) -> dict:
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

# Main function to extract food items from a meal description
def extract_food_items(description: str) -> list[dict]:
    # Prompt engineering to get Gemini to extract food items from natural language description
    response = client.models.generate_content(
        model=MODEL,
        contents=f"""
        Extract food items from this meal description.

        IMPORTANT RULES:
        - ONLY extract foods explicitly mentioned — do NOT guess or substitute
        - Break down composite foods into their main components (e.g., "spaghetti with meat sauce" → "spaghetti, ground beef, tomato sauce")
        - Do NOT change the type of food (e.g., "ham" should stay "ham", NOT "turkey ham")
        - Do NOT convert foods into different foods (e.g., bread ≠ bagel)
        - Preserve the original food as closely as possible
        - Prefer simple, generic food names (e.g., "white rice", "grilled chicken", "cheddar cheese")
        - Avoid brand names unless explicitly mentioned

        PORTIONS:
        - If a quantity is given, use it exactly (e.g., "2 slices", "12 oz")
        - If no quantity is given, assume a reasonable standard portion:
        - meats: 100g
        - carbs (rice, pasta): 1 cup
        - bread: 2 slices
        - sauces/toppings: 1 tbsp
        - NEVER use vague terms like "portion", "serving", or "some"

        OUTPUT FORMAT:
        Return ONLY valid JSON:

        {{
        "items": [
            {{"item": "food name", "amount": "portion size"}}
        ]
        }}

        Meal: "{description}"
        """
    )
    data = extract_json(response.text)
    items = data.get("items", [])

    if isinstance(items, dict):
        items = [items]  # ensure it's always a list

    return items

# Function to look up nutrition info for a given food item using USDA API
def call_usda_api(food_name: str, amount_str: str) -> dict | None:
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
        base_macros = extract_macros(best_match)
        gram_weight = get_portion_in_grams(amount_str, food_name)

        # USDA data is per 100g, so calculate scaling factor
        multiplier = gram_weight / 100.0

        # Return standardized nutrition info - calories, protein, carbs, fat
        return {
            "food_name": best_match["description"],
            "calories": round(base_macros["calories"] * multiplier, 2),
            "protein": round(base_macros["protein"] * multiplier, 2),
            "carbs": round(base_macros["carbs"] * multiplier, 2),
            "fat": round(base_macros["fat"] * multiplier, 2),
            "estimated": False  # indicates whether this is an estimate or exact USDA data
        }
    except Exception as e:
        print(f"USDA API error for '{food_name}': {e}")
        return None

# Fallback function to estimate nutrition info using LLM if USDA lookup fails
def llm_fallback(food_name: str, amount: str) -> dict:
    response = client.models.generate_content(
        model=MODEL,
        contents=f"""
        Estimate nutrition for a single food item.

        FOOD:
        "{amount} of {food_name}"

        RULES:
        - Use standard USDA-style nutrition estimates
        - Use realistic portion assumptions:
        - 1 slice cheese ≈ 20g
        - 1 slice bread ≈ 30g
        - 1 cup rice ≈ 200g
        - 1 oz meat ≈ 28g
        - If the food type is ambiguous (e.g., "cheese"), assume a common default:
        - cheese → cheddar
        - bread → white bread
        - rice → white rice
        - meat → cooked, unbreaded
        - DO NOT assume fried, breaded, or restaurant versions unless specified
        - Keep values realistic (no extreme calorie counts)

        OUTPUT:
        Return ONLY valid JSON:

        {{
            "food_name": "{food_name}",
            "calories": number,
            "protein": number,
            "carbs": number,
            "fat": number
        }}
        """
    )
    print(f"LLM fallback response for {food_name}: {response.text}")
    result = extract_json(response.text)
    result["estimated"] = True  # mark this as an estimate
    return result

# Main function to get nutrition info for a food item and amount
def get_nutrition(food_name: str, amount: str) -> dict:
    # Attempt USDA lookup with scoring first
    nutrition = call_usda_api(food_name, amount)
    if nutrition:
        print(f"USDA match: {nutrition['food_name']}")
        return nutrition
    else:
        print(f"Using LLM fallback for {food_name}")
        return llm_fallback(food_name, amount)

# Main function to parse a meal description and return total nutrition info
def parse_meal(description: str) -> dict:
    """
    Full meal parsing pipeline:
    1. Extract food items from natural languagedescription using Gemini
    2. Look up each item in USDA database
    3. If USDA lookup fails, use LLM fallback to estimate nutrition
    4. Sum total calories, protein, carbs, and fat for the meal

    Input example: "chicken breast with rice and broccoli"
    Output example: {"food_name": "chicken breast, rice, broccoli", "calories": 600, "protein": 50, "carbs": 60, "fat": 10, "has_estimates": False}
    """
    # Step 1: Extract food items
    food_items = extract_food_items(description)
    print(f"Extracted food items: {food_items}")

    # Step 2 & 3: Get nutrition for each item, using USDA or LLM fallback
    total = {
        "food_names": [],
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "has_estimates": False
    }

    for item in food_items:
        nutrition = get_nutrition(item["item"], item["amount"])
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