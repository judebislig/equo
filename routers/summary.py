# routers/summary.py
# Daily summary endpoint — aggregates meals and workouts for the day
# Core feature of Equo — shows calorie balance vs goal
# All routes prefixed with /summary in main.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import cast, Date, func
from database import get_db
from schemas.summary import DailySummaryResponse
from models.meal import Meal
from models.workout import Workout
from models.user import User
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/{user_id}/today", response_model=DailySummaryResponse)
def get_daily_summary(user_id: int, db: Session = Depends(get_db)):
    """
    Get today's calorie summary for a user.
    Aggregates all meals and workouts logged today.
    Returns net calories, remaining calories, and goal status.
    """
    
    # Will use UTC for consistency. Implementing user timezones later.
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=1)

    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    meal_totals = db.query(
        func.coalesce(func.sum(Meal.calories), 0).label("calories"),
        func.coalesce(func.sum(Meal.protein), 0).label("protein"),
        func.coalesce(func.sum(Meal.carbs), 0).label("carbs"),
        func.coalesce(func.sum(Meal.fat), 0).label("fat")
    ).filter(
        Meal.user_id == user_id,
        Meal.logged_at >= start,
        Meal.logged_at <= end
    ).first()

    workout_totals = db.query(
        func.coalesce(func.sum(Workout.calories_burned), 0).label("calories_burned")
    ).filter(
        Workout.user_id == user_id,
        Workout.logged_at >= start,
        Workout.logged_at < end
    ).first()

    return DailySummaryResponse(
        user_id=user_id,
        date=today,
        calorie_target=db_user.calorie_target,
        goal=db_user.goal,
        calories_eaten=round(meal_totals.calories, 1),
        protein_eaten=round(meal_totals.protein, 1),
        carbs_eaten=round(meal_totals.carbs, 1),
        fat_eaten=round(meal_totals.fat, 1),
        calories_burned=round(workout_totals.calories_burned, 1)
    )