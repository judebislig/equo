# models/user.py
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    # Primary key — auto increments
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()
    
    # Physical stats — optional since user might not enter immediately
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Goal settings
    goal: Mapped[str] = mapped_column()  # bulk, cut, maintain
    calorie_target: Mapped[float] = mapped_column()
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)