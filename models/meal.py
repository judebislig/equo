# models/meal.py
# SQLAlchemy model that defines the meals table in PostgreSQL - turns Python object into SQLAlchemy object that can be translated to database (ORM)
# This is NOT a Pydantic schema - it maps directly to a database table

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from database import Base
from core.enums import MealType

class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    meal_type: Mapped[MealType] = mapped_column()   # breakfast, lunch, dinner, snack
    description: Mapped[str] = mapped_column()      # natural language input

    # Returned and parsed from LLM (Gemini Flash)
    food_name: Mapped[str] = mapped_column()
    calories: Mapped[float] = mapped_column()
    protein: Mapped[float] = mapped_column()
    carbs: Mapped[float] = mapped_column()
    fat: Mapped[float] = mapped_column()

    is_estimated: Mapped[bool] = mapped_column(default=False)  # True if macros came from LLM fallback

    logged_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)