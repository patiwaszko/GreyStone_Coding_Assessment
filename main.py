from typing import Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class UserCreate(BaseModel):
    username: str

class UserResponse(BaseModel):
    username: str

# Simulated in-memory database
db = []

@app.post("/users/", response_model=UserResponse)
def create_user(user_create: UserCreate):
    # TODO: DB Read / write
    
    existing_user = user_create in db

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    db.append(user_create)

    return user_create

@app.get("/users/", response_model=List[UserResponse])
def list_users():
    return db
