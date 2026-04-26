# services/prompts.py
# Contains all prompt engineering for interacting with LLMs (Gemini) in a structured way
# We use f-strings or .format() placeholders like {description}

EXTRACT_FOOD_ITEMS_PROMPT = """
Extract food items from this meal description.

IMPORTANT RULES:
- ONLY extract foods explicitly mentioned — do NOT guess or substitute
- Break down composite foods into their main components (e.g., "spaghetti with meat sauce" → "spaghetti, ground beef, tomato sauce")
- Do NOT change the type of food (e.g., "ham" should stay "ham", NOT "turkey ham")
- Do NOT convert foods into different foods (e.g., bread ≠ bagel)
- Preserve the original food as closely as possible
- Prefer simple, generic food names (e.g., "white rice", "grilled chicken", "cheddar cheese")
- Avoid brand names unless explicitly mentioned
- Treat fast food items as single items, not their components
  Example: "mcdonalds chicken nuggets" → {{"item": "mcdonalds chicken nuggets 10 piece", "amount": "10 piece"}}
  NOT: chicken + breading as separate items
- Keep brand names when present — they help with lookup accuracy
- If an item has a clear quantity, include it in the amount field

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

LLM_FALLBACK_PROMPT = """
ACT AS A NUTRITION DATA API.
Your task is to return a JSON ARRAY of nutrition estimates.

CRITICAL REQUIREMENT: 
You must return exactly {count} objects in the array. 
One for each item in this list: {items_json}

STRICT JSON SCHEMA:
[
  {{
    "food_name": "string",
    "calories": number,
    "protein": number,
    "carbs": number,
    "fat": number
  }}
]

DO NOT include any conversational text. 
DO NOT include Markdown formatting (no ```json).
ONLY return the raw JSON array.
"""