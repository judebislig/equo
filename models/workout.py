# models/workout.py
# SQLAlchemy model that defines the users table in PostgreSQL - turns Python object into SQLAlchemy object that can be translated to database (ORM)
# This is NOT a Pydantic schema - it maps directly to a database table

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from database import Base

class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    activity_type: Mapped[str] = mapped_column()   
    duration_minutes: Mapped[int] = mapped_column()
    calories_burned: Mapped[float] = mapped_column()
    is_estimated: Mapped[bool] = mapped_column(default=True)    # False if user manually inputs calories
    notes: Mapped[Optional[str]] = mapped_column(nullable=True) # Free text for workout details
    logged_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)