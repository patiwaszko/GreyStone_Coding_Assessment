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

class LoanCreate(BaseModel):
    amount: float
    apr: float
    term: int
    status: str
    owner_id: int

class LoanResponse(BaseModel):
    id: int
    amount: float
    apr: float
    term: int
    status: str
    owner_id: int

# Simulated in-memory database
users_db = []
loans_db = []
user_id_counter = 1
loan_id_counter = 1
existing_usernames = set()

@app.post("/users/", response_model=UserResponse)
def create_user(user_create: UserCreate):
    global user_id_counter
    
    existing_user = user_create.username in existing_usernames

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_id = user_id_counter
    user_response = UserResponse(id=user_id, username=user_create.username)

    user_id_counter += 1

    users_db.append(user_response)
    existing_usernames.add(user_create.username)

    return user_response

@app.get("/users/", response_model=List[UserResponse])
def list_users():
    return users_db

@app.post("/loans/", response_model=LoanResponse)
def create_loan(loan_create: LoanCreate):
    global loan_id_counter

    if loan_create.amount <= 0:
        raise HTTPException(status_code=400, detail="Loan amount must be greater than zero.")

    if loan_create.apr <= 0:
        raise HTTPException(status_code=400, detail="Loan interest rate must be greater than zero.")

    if loan_create.term <= 0:
        raise HTTPException(status_code=400, detail="Loan term must be greater than zero.")

    if loan_create.status.lower() not in ['active', 'inactive']:
        raise HTTPException(status_code=400, detail="Loan status must be either active or inactive.")

    if loan_create.owner_id > len(users_db) or loan_create.owner_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid owner_id. User does not exist.")

    loan_id = loan_id_counter
    loan_response = LoanResponse(id=loan_id, **loan_create.model_dump())
    loans_db.append(loan_response)

    loan_id_counter += 1

    return loan_response

@app.get("/loans/", response_model=List[UserResponse])
def list_loans():
    return loans_db