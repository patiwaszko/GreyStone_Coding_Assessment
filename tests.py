from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_user():
    response = client.post("/users/", json={"username": "testuser"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "username": "testuser"}
