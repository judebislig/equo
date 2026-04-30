# Sections

1. Title and Description
2. Live demo
3. Architecture overview
4. Key features
5. Tech stack
6. How it works (the pipeline)
7. API endpoints
8. Running locally
9. Environment variables

# Equo - Personal Health Optimization System

A health tracking API that lets users log meals in natural language and receive accurate nutrition data through a multi-stage parsing pipeline. Computes dynamic daily calorie targets based on biometrics and actual workout calories, projecting weekly weight change towards the user's goal.

## Live Demo
API: http://18.224.179.88:8000/docs

## Architecture

User -> FASTAPI (AWS EC2) -> PostgreSQL (Supabase)
        -> stored food cache
        -> Gemini Flash (NLP extraction)
        -> USDA FoodData Central (nutrition lookup)
        -> LLM fallback (unmatched foods)

## Features

- Natural language meal logging - type "chicken rice and broccoli" and get back structured macros
- Multi-stage food parsing pipeline with relevance scoring, Atwater calorie validation / other validation, LLM fallback
- Dynamic TDEE calculation using Mifflin-St Jeor equation with real workout calories layered on top
- Goal-aware daily summary - cut, bulk, or maintain with regards to both maintenance calories and caloric goal to hit per day
- Weekly weight forecast based on net calorie balance (How much weight will change in a week based on current calorie difference)
- MET-based workout calorie calculation with manual user override suport
- Branded food detection - skips USDA for fast food, uses LLM direction
- Note: All weight and height measurements are in metric, while time is measured in UTC to stay consistent.
- Note: A cut is defined as -500 calories deficit and a bulk is defined as +300 calories surplus

## Tech Stack

|       Layer       |       Technology      |
|-------------------|-----------------------|
| Backend           | Python, FastAPI       |
| Database          | PostgreSQL (Supabase) |
| NLP Extraction    | Gemini Flash          |
| Nutrition Data    | USDA FoodData Central |
| Containerization  | Docker                |
| Hosting           | AWS EC2               |

## How the Food Parsing Pipeline Works

1. **Extraction** - User submits a natural language description ("double cheeseburger with fries"). Gemini Flash extracts individual food items and estimated portions as structured JSON. If no portion size is provided from the user, it assumes a portion size of 100g.
2. **Branded food detection** - If the item contains a known fast food brand, USDA lookup is skipped entirely and the item goes straight to LLM estimation. USDA's Foundation and SR Legacy databases don't contain branded items reliably.
3. **USDA lookup** - For unbranded whole foods, the pipeline queries USDA FoodData Central and scores results by relevance using token overlap between the query and result description.
4. **Validation** - USDA results are validated against physiological bounds - Atwater calorie math, category-specific carb limits (meat shouldn't have > 12g carbs/100g), and a calorie ceiling of 950 kcal/100g (pure fat limit). Failed results fall through to LLM.
5. **LLM fallback** - Items that fail USDA lookup or validation are batched into a single Gemini request for estimation. Results are flagged as estimated in the response.
6. **Caching** - Successful lookups are cached to a JSON file to avoid redundant API calls for repeated items.
7. **Aggregation** - Individual item macros are summed and returned as a unified meal response with food names, total macros, and an is_estimated flag.

## API Endpoints

### Users
| Method | Endpoint     | Description                           |
|--------|--------------|---------------------------------------|
| POST   | /users       | Create user with autocalculated TDEE  |
| GET    | /users/{id}  | Get user profile                      |
| PUT    | /users/{id}  | Update stats, recalculates TDEE       |
| DELETE | /users/{id}  | Delete a user                         |

### Meals
| Method | Endpoint                 | Description                   |
|--------|--------------------------|-------------------------------|
| POST   | /meals/parse             | Preview macros without saving |
| POST   | /meals                   | Parse and log a meal          |
| GET    | /meals/{user_id}/today   | Today's meals                 |
| GET    | /meals/{user_id}/history | All meals, newest first       |
| DELETE | /meals/{id}              | Delete a meal                 |

### Workouts
| Method | Endpoint                     | Description                               |
|--------|------------------------------|-------------------------------------------|
| POST   | /workouts                    | Log workout, calculates calories via MET  |
| GET    | /workouts/{user_id}/today    | Today's workouts                          |
| GET    | /workouts/{user_id}/history  | All workouts, newest first                |
| DELETE | /workouts/{id}               | Delete a workout                          |

### Summary
| Method | Endpoint                 | Description                                           |
|--------|--------------------------|-------------------------------------------------------|
| GET    | /summary/{user_id}/today | Daily calorie balance, goal status, weekly forecast   |

## Running Locally

**Prerequisites:** Python 3.12+, Docker

1. Clone the repo
```bash
   git clone https://github.com/judebislig/equo.git
   cd equo
```

2. Create .env file
- DATABASE_URL=postgresql://postgres:[PASSWORD]@your-supabase-url:6543/postgres
- GEMINI_API_KEY=your_gemini_key_here
- USDA_API_KEY=your_usda_key_here

3. Run with Docker
```bash
   docker compose up --build
```

4. Visit http://localhost:8000/docs

## Environment Variables

| Variable          | Description                                               |
|-------------------|-----------------------------------------------------------|
| DATABASE_URL      | Supabase PostgreSQL transaction pooler URL                |
| GEMINI_API_KEY    | Google Gemini Flash API key (free at aistudio.google.com) |
| USDA_API_KEY      | USDA FoodData Central API key (free at fdc.nal.usda.gov)  |