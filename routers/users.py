# routers/user.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import UserCreate, UserUpdate, UserResponse
from models.user import User


@app.post("/users")
def create_user(user: User):
    users.append(user)
    return users


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int) -> User:
    if user_id < len(users):
        return users[user_id]
    else:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    

@app.put("/users/{user_id}")
def update_stats():