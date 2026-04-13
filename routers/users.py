# routers/user.py
# Defines all API endpoints related to users

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import UserCreate, UserUpdate, UserResponse
from models.user import User

router = APIRouter()

# Create a new user
@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        name = user.name,
        age = user.age,
        weight = user.weight,
        height = user.height,
        goal = user.goal,
        calorie_target = user.calorie_target
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Gets a single user by ID
# Returns 404 if user does not exist
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    return db_user
    

# Update an existing user's stats or goal
# Only updates fields that are provided - ignores None values
# Returns 404 if user does not exist
@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # only update fields that were actually provided
    # None means the client didn't send that field - leave it unchanged
    if user.weight is not None:
        db_user.weight = user.weight
    if user.height is not None:
        db_user.height = user.height
    if user.goal is not None:
        db_user.goal = user.goal
    if user.calorie_target is not None:
        db_user.calorie_target = user.calorie_target