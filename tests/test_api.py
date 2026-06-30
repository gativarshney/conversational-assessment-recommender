from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint() -> None:
    """Test that GET /health returns HTTP 200 and the expected status JSON."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_chat_endpoint_mock_response() -> None:
    """Test that POST /chat returns a valid response matching the Pydantic schema."""
    payload = {
        "messages": [
            {"role": "user", "content": "I am hiring a mid-level Java developer."}
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert "end_of_conversation" in data
    assert isinstance(data["end_of_conversation"], bool)
    assert data["end_of_conversation"] is False

def test_chat_endpoint_validation_error() -> None:
    """Test that POST /chat fails with validation error (HTTP 422) if fields are missing."""
    payload = {}  # Missing 'messages' list
    response = client.post("/chat", json=payload)
    assert response.status_code == 422
