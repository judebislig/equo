# main.py
# Entry point for the Equo API
# Responsible for startup tasks and wiring together all routers

from fastapi import FastAPI, HTTPException
from database import engine, Base
from pydantic import BaseModel
from dotenv import load_dotenv
import models.user

# Load environment variables from .env file
# Makes DATABASE_URL, ANTHROPIC_API_KEY, etc available to all modules
load_dotenv()

# Create the SQLAlchemy engine
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Equo")

# class Item(BaseModel):
#     text: str
#     is_done: bool = False

# items = []

@app.get("/")
def root():
    return {"Message": "Equo API is running"}

# @app.post("/items")
# def create_item(item: Item):
#     items.append(item)
#     return items

# @app.get("/items", response_model=list[Item])
# def list_items(limit: int = 10):
#     return items[0:limit]

# @app.get("/items/{item_id}", response_model=Item)
# def get_item(item_id: int) -> Item:
#     if item_id < len(items):
#         return items[item_id]
#     else:
#         raise HTTPException(status_code=404, detail=f"Item {item_id} not found")