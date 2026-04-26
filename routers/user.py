# routers/user.py
# Defines all API endpoints related to users

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import UserCreate, UserUpdate, UserResponse
from models.user import User
from core.enums import GoalType
from services.activity_calories import get_initial_calorie_target

router = APIRouter()

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user with the provided information
    Returns the created user object
    """
    # Calculate target before saving
    target = get_initial_calorie_target(user.weight, user.height, user.sex, user.goal)

    # New SQLAlchemy User object from validated Python object (from Pydantic)
    db_user = User(
        name = user.name,
        age = user.age,
        sex = user.sex,
        weight = user.weight,
        height = user.height,
        goal = user.goal,
        calorie_target=target
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Gets a single user by ID
    Returns 404 if user does not exist
    """
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    return db_user
    
@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """
    Update an existing user's stats or goal
    Only updates fields that are provided - ignores None values
    Returns 404 if user does not exist
    """
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # 1. Convert incoming Pydantic model to a dict, ignoring unset fields
    update_data = user.model_dump(exclude_unset=True)

    # 2. Check if we need to recalculate the calorie target
    # Any change to these 4 fields affects the baseline math
    trigger_fields = {"weight", "height", "goal", "age"}
    
    if any(field in update_data for field in trigger_fields) and "calorie_target" not in update_data:
        # We use the new value if provided, otherwise fallback to existing DB value
        new_weight = update_data.get("weight", db_user.weight)
        new_height = update_data.get("height", db_user.height)
        new_goal = update_data.get("goal", db_user.goal)
        new_age = update_data.get("age", db_user.age)
        
        # Recalculate!
        update_data["calorie_target"] = get_initial_calorie_target(
            weight_kg=new_weight,
            height_cm=new_height,
            age=new_age,
            sex=db_user.sex,  # Sex is usually immutable, so we pull from DB
            goal=new_goal
        )

    # 3. Apply all updates to the DB object
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    delete a user by ID
    Returns a success message or 404 if user does not exist
    """
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    db.delete(db_user)
    db.commit()

    return {"message": f"User {user_id} deleted successfully"}