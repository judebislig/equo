# models/user.py
# SQLAlchemy model that defines the users table in PostgreSQL - turns Python object into SQLAlchemy object that can be translated to database (ORM)
# This is NOT a Pydantic schema - it maps directly to a database table

from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from database import Base
from core.enums import GoalType

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()
    sex: Mapped[str] = mapped_column()  # male, female
    weight: Mapped[Optional[float]] = mapped_column(nullable=True)
    height: Mapped[Optional[float]] = mapped_column(nullable=True)
    goal: Mapped[GoalType] = mapped_column()  # bulk, cut, maintain. Maintain is default for now
    calorie_target: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)