# routers/meal.py
# Defines all API endpoints related to users

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session
from database import get_db
from schemas.meal import MealCreate, MealResponse
from models.meal import Meal
from core.enums import MealType
from datetime import datetime, date

router = APIRouter()

# Parse a meal description and return macros without saving to database
# Useful for previewing what Gemini + USDA will return before committing
@router.post("/parse", response_model=dict)
def preview_meal(description: str, db: Session = Depends(get_db)):
    result = parse_meal(description)
    return result

# Parse a meal description and save to the database
# Calls Gemini to extract food items, looks up each in USDA database, sums macros, saves result linked to user
@router.post("/", response_model=MealResponse)
def log_meal(meal: MealCreate, db: Session = Depends(get_db)):
    parsed = parse_meal(meal.description)
    
    # New SQLAlchemy Meal object from validated Python object (from Pydantic)
    db_meal = Meal(
        user_id=meal.user_id,
        meal_type=meal.meal_type,
        description=meal.description,
        food_name=parsed["food_name"],
        calories=parsed["calories"],
        protein=parsed["protein"],
        carbs=parsed["carbs"],
        fat=parsed["fat"],
        estimated=parsed["has_estimates"]   # store whether any item was estimated
    )
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal

# Get all meals logged by a user today
# Filtered by user_id and today's date
@router.get("/{user_id}/today", response_model=list[MealResponse])
def get_todays_meals(user_id: int, db: Session = Depends(get_db)):
    today = date.today()

    meals = db.query(Meal).filter(
        Meal.user_id == user_id,
        cast(Meal.logged_at, Date) == today
    ).all()

    if not meals:
        raise HTTPException(status_code=404, detail=f"No meals found for user {user_id} today")

    return meals

# Get all means ever logged by a user
# Returns in reverse chronological order - most recent first
@router.get("/{user_id}/history", response_model=list[MealResponse])
def get_meal_history(user_id: int, db: Session = Depends(get_db)):
    meals = db.query(Meal).filter(
        Meal.user_id == user_id
    ).order_by(Meal.logged_at.desc()).all()

    if not meals:
        raise HTTPException(status_code=404, detail=f"No meals found for user {user_id}")

    return meals

# Delete a meal given an id
@router.delete("/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    db_meal = db.query(Meal).filter(Meal.id == meal_id).first()

    if not db_meal:
        raise HTTPException(status_code=404, detail=f"Meal {meal_id} not found")
    
    db.delete(db_meal)
    db.commit()

    return {"message": f"Meal {meal_id} deleted successfully"}