# routers/workout.py
# Defines all API endpoints related to workouts

from fastapi import APIRouter, Depends, HTTPException
from models.user import User
from services.activity_calories import calculate_calories_burned
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session
from database import get_db
from schemas.workout import WorkoutCreate, WorkoutResponse
from models.workout import Workout
from core.enums import ActivityType
from datetime import datetime, date, timedelta

router = APIRouter()

@router.post("/", response_model=WorkoutResponse)
def log_workout(workout: WorkoutCreate, db: Session = Depends(get_db)):
    """
    Log a workout for a user.
    Fetches user weight to calculate calories burned via MET formula.
    If calories_override is provided uses that instead.
    """

    db_user = db.query(User).filter(User.id == workout.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail=f"user {workout.user_id} is not found")
    
    # Calculate calories - uses override if provided, otherwise MET formula
    weight_kg = db_user.weight or 70.0 # default 70kg if weight is not set
    calories, is_estimated = calculate_calories_burned(
        activity_type=workout.activity_type,
        duration_minutes=workout.duration_minutes,
        weight_kg=weight_kg,
        calories_override=workout.calories_override
    )

    # Create workout record combining user input and calculated calories
    db_workout = Workout(
        user_id=workout.user_id,
        activity_type=workout.activity_type,
        duration_minutes=workout.duration_minutes,
        calories_burned=calories,
        is_estimated=is_estimated,
        notes=workout.notes
    )

    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout