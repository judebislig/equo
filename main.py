# main.py
# Entry point for the Equo API
# Responsible for startup tasks and wiring together all routers

from fastapi import FastAPI
from database import engine, Base
from dotenv import load_dotenv
from routers import users
import models.user

# Load environment variables from .env file
# Makes DATABASE_URL, ANTHROPIC_API_KEY, etc available to all modules
load_dotenv()

# Create the SQLAlchemy engine
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Equo")

@app.get("/")
def root():
    return {"Message": "Equo API is running"}

app.include_router(users.router, prefix="/users", tags=["users"])


    