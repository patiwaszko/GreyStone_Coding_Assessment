import pytest
from fastapi.testclient import TestClient
from main import app, users_db, loans_db, user_loan_db, loan_exists_for_user

client = TestClient(app)

def test_create_user():
    response = client.post("/users/", json={"username": "testuser"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "username": "testuser"}

def test_create_existing_user():
    client.post("/users/", json={"username": "existinguser"})
    response = client.post("/users/", json={"username": "existinguser"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already exists"}

def test_list_users():
    client.post("/users/", json={"username": "user1"})
    client.post("/users/", json={"username": "user2"})
    response = client.get("/users/")
    assert response.status_code == 200
    assert len(response.json()) == 4

def test_create_loan():
    response = client.post(
        "/loans/",
        json={
            "amount": 1000.0,
            "apr": .05,
            "term": 12,
            "status": "active",
            "owner_id": 1,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "amount": 1000.0,
        "apr": .05,
        "term": 12,
        "status": "active",
        "owner_id": 1,
    }

def test_create_invalid_loan():
    response = client.post(
        "/loans/",
        json={
            "amount": 0.0,
            "apr": 5.0,
            "term": 12,
            "status": "active",
            "owner_id": 1,
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Loan amount must be greater than zero."}

def test_list_loans():
    response = client.get("/loans/")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_user_loans():
    client.post("/users/", json={"username": "user1"})
    response = client.get("/users/1/loans")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_loan_schedule():
    response = client.get("/loans/1?user_id=1")
    assert response.status_code == 200
    assert len(response.json()) == 12

def test_get_loan_summary():
    response = client.get("/loans/1/summary/6?user_id=1")
    assert response.status_code == 200
    assert response.json() == {
        "current_principal": 506.2366917469525,
        "aggregate_principal_paid": 493.7633082530474,
        "aggregate_interest_paid": 19.8815824777574,
    }

def test_share_loan():
    response = client.post("/loans/1/share?owner_id=1&user_id=2")
    assert response.status_code == 200
    assert response.json() == {"message": "Loan 1 shared with user 2"}

def test_share_loan_invalid_owner():
    response = client.post("/loans/1/share?owner_id=2&user_id=2")
    assert response.status_code == 403
    assert response.json() == {"detail": "User does not have access to share this loan"}

def test_share_loan_invalid_user():
    response = client.post("/loans/1/share?owner_id=1&user_id=7")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_loan_exists_for_user():
    assert loan_exists_for_user(1, 1)
    assert loan_exists_for_user(2, 1)
    assert not loan_exists_for_user(3, 1)
    assert not loan_exists_for_user(1, 2)