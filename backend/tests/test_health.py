import os

from fastapi.testclient import TestClient

# Mock environment variables for testing
os.environ["META_ACCESS_TOKEN"] = "test_token"
os.environ["META_AD_ACCOUNT_ID"] = "act_123456"
os.environ["LLM_PROVIDER"] = "openrouter"
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-test-key"
os.environ["POSTGRES_DSN"] = "postgresql+asyncpg://user:pass@localhost/db"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/db"

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
