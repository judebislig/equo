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