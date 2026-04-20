# services/nutrition.py
# Handles all food parsing and nutrition lookup logic
# Flow: natural language -> Gemini extracts items -> USDA looks up nutrition / LLM fallback -> return
# Caching can be added later as an optimization

import httpx
import json
import os
from core.food_logic import get_portion_in_grams, calculate_relevance_score, validate_macro_logic
from services.prompts import EXTRACT_FOOD_ITEMS_PROMPT, LLM_FALLBACK_PROMPT
from google import genai

# Load environment variables for API keys
USDA_API_KEY = os.getenv("USDA_API_KEY")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-flash-latest"
DEBUG_MODE = False  # Set to True to enable debug mock functions instead of actual API calls

# ==========================================
# 1. UTILITIES & JSON HELPERS
# ==========================================

def parse_json_from_text(text: str) -> list | dict:
    """
    Improved parser that handles both JSON Arrays [] and Objects {} 
    while stripping Markdown code blocks.
    """
    # 1. Clean up Markdown formatting if present
    text = text.replace("```json", "").replace("```", "").strip()

    decoder = json.JSONDecoder()

    for i, char in enumerate(text):
        # Look for the start of an Array OR an Object
        if char in ("{", "["):
            try:
                obj, _ = decoder.raw_decode(text[i:])
                return obj
            except json.JSONDecodeError:
                continue

    raise ValueError(f"No JSON object or array found in the text: {text[:100]}...")

def mock_extract_ingredients(description: str) -> list[dict]:
    """
    Mock function to simulate Gemini's ingredient extraction for testing purposes
    """
    print(f"Mock extracting ingredients from: {description}")
    return [
        {"item": "ham", "amount": "100g"},
        {"item": "cinnamon raisin bread", "amount": "2 slices"},
        {"item": "cheese", "amount": "2 slices"}
    ]

def mock_llm_fallback(food_name: str, amount: str) -> dict:
    """
    Mock function to simulate LLM fallback for testing purposes
    """
    print(f"Mock LLM fallback for {food_name} with amount {amount}")
    return {
        "food_name": food_name,
        "calories": 100,
        "protein": 10,
        "carbs": 10,
        "fat": 2,
        "estimated": True
    }

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

    # 1. Get base calories using multiple possible keys to handle variations in USDA data
    base_cal = (
        nutrients.get("energy (kcal)") or 
        nutrients.get("energy", 0) or
        next((n.get("value") for n in food_data.get("foodNutrients", [])
            if "energy" in n.get("nutrientName", "").lower() and n.get("unitName") == "KCAL"), 0)
    )

    # 2. Determine the "Data Base Unit"
    # Branded foods provide 'serviceSize' (e.g. 28 for 28g), while Foundation foods are typically per 100g
    serving_size = food_data.get("servingSize")

    # If a serving size exists and isn't 100, normalize data back to 100g
    # For example, if 740 cals is for a 200g wedge, normaliation_factor = 100/200 = 0.5
    # 740 cals * 0.5 = 370 cals per 100g, which is more comparable to other items
    normalization_factor = 1.0
    if serving_size and serving_size > 0 and serving_size != 100:
        normalization_factor = 100.0 / serving_size

    return {
        "calories_per_100g": base_cal * normalization_factor,
        "protein_per_100g": nutrients.get("protein", 0) * normalization_factor,
        "carbs_per_100g": round(max(0, nutrients.get("carbohydrate, by difference", 0) * normalization_factor), 1),
        "fat_per_100g": nutrients.get("total lipid (fat)", 0) * normalization_factor
    }

# ==========================================
# 3. EXTERNAL CLIENTS (USDA & GEMINI)
# ==========================================

def nlp_extract_ingredients(description: str) -> list[dict]:
    """
    Main function to extract food items from a meal description
    Returns a list of dicts with "item" and "amount" keys, e.g., [{"item": "chicken breast", "amount": "150g"}, ...]
    """
    if DEBUG_MODE:
        return mock_extract_ingredients(description)

    prompt = EXTRACT_FOOD_ITEMS_PROMPT.format(description=description)
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    data = parse_json_from_text(response.text)
    items = data.get("items", [])

    if isinstance(items, dict):
        items = [items]  # ensure it's always a list

    return items

def estimate_nutrition_batch(items: list[dict]) -> list[dict]:
    """
    Takes a list of items that failed USDA lookup and estimates nutrition for each using a single Gemini request
    """
    if not items:
        return []
    
    if DEBUG_MODE:
        print(f"Mock estimating nutrition for batch: {items}")
        return [mock_llm_fallback(i["item"], i["amount"]) for i in items]
    
    # Real LLM logic
    # We send the entire batch of items in one prompt to Gemini, which should be more efficient than multiple calls
    items_json = json.dumps(items)
    print(items_json)

    prompt = LLM_FALLBACK_PROMPT.format(count=len(items), items_json=items_json)
    response = client.models.generate_content(model=MODEL, contents=prompt)

    # Extract JSON array of nutrition estimates from the response
    results = parse_json_from_text(response.text)

    print(f"Items - {items}")
    print(f"Results - {results}")

    if isinstance(results, dict):
        results = [results]  # ensure it's always a list

    for r in results:
        r["estimated"] = True  # mark these as estimates

    return results

def is_usda_data_sane(food_name: str, macros_per_100g: dict) -> bool:
    print(f"Sanity checking USDA data for '{food_name}': {macros_per_100g} kcal per 100g")
    name = food_name.lower()
    cals = macros_per_100g["calories_per_100g"]

    # Check Atwater math
    if not validate_macro_logic(macros_per_100g):
        print(f"USDA data for '{food_name}' failed Atwater calorie validation for {food_name}")
        return False

    # Example sanity check: pure fat is 900kcal/100g. If the base is higher than 950,
    # the USDA entry is likely using a non-standard unit (like 'per pound')
    if cals > 950:
        print(f"USDA data for '{food_name}' has unusually high calories ({macros_per_100g} kcal), likely due to non-standard serving size.")
        return False
    
    # Leafy greens or very low-calorie items should not have high calories per 100g
    if any(x in name for x in ["spinach", "kale", "lettuce", "broccoli", "cucumber", "cabbage"]) and cals > 120:
        return False
    
    # Pure meat should not have much carbs
    if any(x in name for x in ["chicken", "beef", "pork", "ham", "turkey", "sausage", "lamb"]) and macros_per_100g.get("carbs_per_100g", 0) > 10:
        return False

    # Dry pasta check
    if "pasta" in name and cals > 400:
        print(f"USDA data for '{food_name}' has unusually high calories ({macros_per_100g} kcal), likely due to being dry pasta. This can be misleading for users who typically eat cooked pasta.")
        return False

    return True

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
        "dataType": "Foundation,SR Legacy"
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

        if not is_usda_data_sane(food_name, base_macros):
            print(f"USDA data for '{food_name}' failed sanity check, skipping to LLM fallback")
            return None

        gram_weight = get_portion_in_grams(food_name, amount_str)

        # USDA data is per 100g, so calculate scaling factor
        multiplier = gram_weight / 100.0

        # Return standardized nutrition info - calories, protein, carbs, fat
        return {
            "food_name": best_match["description"],
            "calories": round(base_macros["calories_per_100g"] * multiplier, 2),
            "protein": round(base_macros["protein_per_100g"] * multiplier, 2),
            "carbs": round(base_macros["carbs_per_100g"] * multiplier, 2),
            "fat": round(base_macros["fat_per_100g"] * multiplier, 2),
            "estimated": False  # indicates this is an exact USDA data
        }
    except Exception as e:
        print(f"USDA API error for '{food_name}': {e}")
        return None

# ==========================================
# 4. THE MAIN PIPELINE
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

    final_nutrition_data = []
    fallback_items_queue = []

    # Step 2: Get nutrition for each item, using USDA or LLM fallback
    for item in food_items:
        # Get nutrition info for this item and amount, including food name, calories, protein, carbs, fat, and whether it was an estimate
        usda_nutrition = call_usda_api(item["item"], item["amount"])
    
        if usda_nutrition:
            # Add original name for UI consistency
            usda_nutrition["display_name"] = item["item"].capitalize()
            final_nutrition_data.append(usda_nutrition)

        else:
            # If failed USDA or hit the 950 calorie sanity check, add to LLM batch list
            fallback_items_queue.append(item)

    # Step 3: The batch fallback to LLM for any items that failed USDA lookup or had poor matches
    if fallback_items_queue:
        print(f"Batch LLM fallback for items: {fallback_items_queue}")
        batch_results = estimate_nutrition_batch(fallback_items_queue)
        
        for i in range(min(len(batch_results), len(fallback_items_queue))):
            est = batch_results[i]
            original_item = fallback_items_queue[i]

            est["display_name"] = original_item["item"].capitalize()
            final_nutrition_data.append(est)

    # Step 4: Aggregation - sum up total calories, protein, carbs, and fat for the whole meal
    meal_summary = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "food_names": [], "has_estimates": False}

    for entry in final_nutrition_data:
        print(f"Adding {entry['display_name']} - Calories: {entry['calories']}, Protein: {entry['protein']}, Carbs: {entry['carbs']}, Fat: {entry['fat']}, Estimated: {entry['estimated']}")
        # Keep track of food names and sum up macros for the whole meal
        meal_summary["food_names"].append(entry.get("display_name", entry.get("food_name", "Unknown Item")))
        meal_summary["calories"] += entry.get("calories", 0)
        meal_summary["protein"] += entry.get("protein", 0)
        meal_summary["carbs"] += max(0, entry.get("carbs", 0)) # ensure carbs don't go negative due to rounding
        meal_summary["fat"] += entry.get("fat", 0)

        # If any item was estimated, mark the whole meal as having estimates
        if entry.get("estimated"):
            meal_summary["has_estimates"] = True

    return {
        "food_name": ", ".join(meal_summary["food_names"]),
        "calories": round(meal_summary["calories"]),
        "protein": round(meal_summary["protein"], 1),
        "carbs": round(max(0, meal_summary["carbs"]), 1),  # carbs can sometimes be negative due to rounding, so we ensure it's not below 0
        "fat": round(meal_summary["fat"], 1),
        "has_estimates": meal_summary["has_estimates"]
    }