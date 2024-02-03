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

class LoanScheduleResponse(BaseModel):
    month: int
    open_balance: float
    total_payment: float
    principal_payment: float
    interest_payment: float
    close_balance: float

class LoanSummaryResponse(BaseModel):
    current_principal: float
    aggregate_principal_paid: float
    aggregate_interest_paid: float

# Simulated in-memory database
users_db = {}
loans_db = {}
user_loan_db = {}
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

    users_db[user_id] = user_response
    user_loan_db[user_id] = []

    existing_usernames.add(user_create.username)
    
    user_id_counter += 1

    return user_response

@app.get("/users/", response_model=List[UserResponse])
def list_users():
    return users_db.values()

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
    
    loans_db[loan_id] = loan_response
    
    user_loan_db[loan_response.owner_id].append(loan_response)

    loan_id_counter += 1

    return loan_response

@app.get("/loans/", response_model=List[LoanResponse])
def list_loans():
    return loans_db.values()

def calculate_loan_schedule(loan):
    amount = loan.amount
    apr = loan.apr
    term = loan.term
    
    monthly_interest_rate = apr / 12

    monthly_payment = (
        amount
        * monthly_interest_rate
        * (1 + monthly_interest_rate) ** term
    ) / ((1 + monthly_interest_rate) ** term - 1)

    remaining_balance = amount
    loan_schedule = []

    for month in range(1, term + 1):
        interest_payment = remaining_balance * monthly_interest_rate
        principal_payment = monthly_payment - interest_payment
        remaining_balance -= principal_payment

        loan_schedule.append(
            LoanScheduleResponse(
                month=month,
                open_balance=remaining_balance + principal_payment,
                total_payment=monthly_payment,
                principal_payment=principal_payment,
                interest_payment=interest_payment,
                close_balance=max(0, remaining_balance),
            )
        )

    return loan_schedule

@app.get("/users/{user_id}/loans", response_model=List[LoanResponse])
def get_user_loans(user_id: int):
    if user_id <= 0 or user_id > len(users_db):
        raise HTTPException(status_code=404, detail="User not found")

    user_loans = user_loan_db[user_id]
    return user_loans


@app.get("/loans/{loan_id}", response_model=List[LoanScheduleResponse])
def get_loan_schedule(loan_id: int, user_id: int):
    loan = loans_db.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if loan.owner_id != user_id:
        raise HTTPException(status_code=403, detail="User does not have access to this loan")

    loan_schedule = calculate_loan_schedule(loan)

    return loan_schedule

@app.get("/loans/{loan_id}/summary/{month}", response_model=LoanSummaryResponse)
def get_loan_summary(loan_id: int, month: int, user_id: int):
    loan = loans_db.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if loan.owner_id != user_id:
        raise HTTPException(status_code=403, detail="User does not have access to this loan")

    if month < 1 or month > loan.term:
        raise HTTPException(status_code=400, detail="Invalid month for loan summary")

    remaining_balance = loan.amount
    monthly_interest_rate = loan.apr / 12
    monthly_payment = (
        remaining_balance
        * monthly_interest_rate
        * (1 + monthly_interest_rate) ** loan.term
    ) / ((1 + monthly_interest_rate) ** loan.term - 1)

    current_principal = remaining_balance
    aggregate_principal_paid = 0
    aggregate_interest_paid = 0

    for current_month in range(1, month + 1):
        interest_payment = remaining_balance * monthly_interest_rate
        principal_payment = min(monthly_payment - interest_payment, remaining_balance)
        remaining_balance -= principal_payment

        current_principal = remaining_balance
        aggregate_principal_paid += principal_payment
        aggregate_interest_paid += interest_payment

    loan_summary = LoanSummaryResponse(
        current_principal=current_principal,
        aggregate_principal_paid=aggregate_principal_paid,
        aggregate_interest_paid=aggregate_interest_paid,
    )

    return loan_summary