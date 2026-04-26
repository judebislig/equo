# routers/workout.py
# Defines all API endpoints related to workouts

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session
from database import get_db
from schemas.workout import WorkoutCreate, WorkoutResponse
from models.workout import Workout
from core.enums import ActivityType
from datetime import datetime, date, timedelta

router = APIRouter()

