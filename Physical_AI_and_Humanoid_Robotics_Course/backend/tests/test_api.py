from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI backend! Access API at /api"}

def test_read_api_root():
    response = client.get("/api")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the API router!"}

def test_chat_endpoint_placeholder():
    response = client.post("/api/chat", json={"question": "What is physical AI?"})
    assert response.status_code == 200
    assert "Based on the textbook content" in response.json()["answer"]

def test_personalize_endpoint_unauthenticated():
    response = client.post("/api/personalize", json={"chapter_id": "intro"})
    assert response.status_code == 401 # Unauthorized expected

def test_translate_endpoint_unauthenticated():
    response = client.post("/api/translate", json={"content": "Hello", "target_language": "ur"})
    assert response.status_code == 401 # Unauthorized expected
