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