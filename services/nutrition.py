# services/nutrition.py
# Handles all food parsing and nutrition lookup logic
# Flow: natural language -> Gemini extracts items -> USDA looks up nutrition -> return
# Caching can be added later as an optimization

import httpx
import json
import os
import google.generativeai as genai
from google.generativeai import GenerationConfig

# Initialize Gemini client with API key from environment variable
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-1.5-flash", 
                              generation_config=GenerationConfig(
                                  response_mime_type="application/json"
                              ))

USDA_API_KEY = os.getenv("USDA_API_KEY")

# Main function to extract food items from a meal description
def extract_food_items(description: str) -> list[str]:
    # Prompt engineering to get Gemini to extract food items from natural language description
    prompt = f"""
    Extract the food items from this meal description: '{description}'. 
    Return as a JSON array:
    [{{"item": "food name", "amount": "portion size"}}]
    
    If no amount is specified, estimate a standard single portion. 
    Be specific - "chicken" should become "chicken breast" or "chicken thigh" if possible.
    """
    response = model.generate_content(prompt)
    try:
        food_items = json.loads(response.text)
        if isinstance(food_items, list):
            return food_items
        else:
            return []
    except json.JSONDecodeError:
        return []
    

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
    nutrients = {n["nutritionName"].lower(): n["value"] for n in food_data.get("foodNutrients", [])}

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
    prompt = f"""
    Estimate the calories, protein, carbs, and fat for: "{amount} of {food_name}".

    Return a JSON object:
    {{
        "food_name": "{food_name}",
        "calories": estimated calories,
        "protein": estimated protein,
        "carbs": estimated carbs,
        "fat": estimated fat,
    }}

    Use standard nutritional values. All numbers should be reasonable estimates for the given portion size.
    """

    response = model.generate_content(prompt)
    result = json.loads(response.text)
    result["estimated"] = True  # mark this as an estimate
    return result


