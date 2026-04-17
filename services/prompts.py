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
Estimate nutrition for each of these items INDIVIDUALLY: {items_list}
Return a JSON array with EXACTLY {count} objects. 
Do not combine items.

RULES:
- Use standard USDA-style estimates.
- Assumptions: 1 slice cheese (20g), 1 slice bread (30g), 1 cup rice (200g).
- Defaults: cheese=cheddar, bread=white, rice=white, meat=cooked/unbreaded.
- Return ONLY a JSON array of objects.

JSON Keys: "food_name", "calories", "protein", "carbs", "fat"
"""