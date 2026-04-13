# routers/user.py
# Defines all API endpoints related to users

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import UserCreate, UserUpdate, UserResponse
from models.user import User
from core.enums import GoalType

router = APIRouter()

# Create a new user
@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # New SQLAlchemy User object from validated Python object (from Pydantic)
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
    update_data = user.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user