from typing import Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class UserCreate(BaseModel):
    username: str

class UserResponse(BaseModel):
    id: int
    username: str

# Simulated in-memory database
db = []
user_id_counter = 1
existing_usernames = set()

@app.post("/users/", response_model=UserResponse)
def create_user(user_create: UserCreate):
    global user_id_counter
    
    existing_user = user_create.username in existing_usernames

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_response = UserResponse(id=user_id_counter, username=user_create.username)

    user_id_counter += 1

    db.append(user_response)
    existing_usernames.add(user_create.username)

    return user_response

@app.get("/users/", response_model=List[UserResponse])
def list_users():
    return db


