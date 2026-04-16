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
def call_usda_api(food_name: str) -> dict | None:
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "query": food_name,
        "api_key": USDA_API_KEY,
        "pageSize": 1,
        "dataType": "SR Legacy,Foundation" 
    }

    response = httpx.get(url, params=params)
    data = response.json()
    if not data.get("foods"):
        print(f"No USDA data found for {food_name}")
        return None
    
    food_data = data["foods"][0]
    
    # Convert nutrition list to a dict for easier access
    nutrients = {}

    for n in food_data.get("foodNutrients", []):
        name = n.get("nutrientName", "").lower()
        value = n.get("value")

        if value is None:
            # Some nutrients might not have a value, skip those
            continue

        nutrients[name] = value

    # Return standardized nutrition info - calories, protein, carbs, fat
    return {
        "food_name": food_data["description"],
        "calories": nutrients.get("energy", 0),
        "protein": nutrients.get("protein", 0),
        "carbs": nutrients.get("carbohydrate, by difference", 0),
        "fat": nutrients.get("total lipid (fat)", 0),
        "estimated": False  # indicates whether this is an estimate or exact USDA data
    }

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
    nutrition = call_usda_api(food_name)
    if nutrition:
        print(f"USDA data found for {food_name}: {nutrition}")
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