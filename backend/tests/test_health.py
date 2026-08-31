from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "database" in body
    assert "llm_configured" in body
    assert "llm_provider" in body
    assert "llm_model" in body
    assert "llm_status" in body
    assert body["llm_provider"] == "ollama"
