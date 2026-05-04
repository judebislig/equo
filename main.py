# main.py
# Entry point for the Equo API
# Responsible for startup tasks and wiring together all routers

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from dotenv import load_dotenv
from routers import user, meal, workout, summary
import models.user
import models.meal
import models.workout

# Load environment variables from .env file
# Makes DATABASE_URL, ANTHROPIC_API_KEY, etc available to all modules
load_dotenv()

# Create the SQLAlchemy engine
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Equo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://18.224.179.88", "http://18.224.179.88:80",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"Message": "Equo API is running"}

app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(meal.router, prefix="/meals", tags=["meals"])
app.include_router(workout.router, prefix="/workouts", tags=["workouts"])
app.include_router(summary.router, prefix="/summary", tags=["summary"])