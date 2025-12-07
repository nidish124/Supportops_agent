from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

"""def test_support_triage():
    test_payload = {
        "request_id": "r1",
        "user_id": "u1",
        "channel": "email",
        "message": "test",
        "severity": "high",
    }
    r = client.post("/support/triage", json=test_payload)
    assert r.status_code == 500
    assert r.json() == {"message": "Not Implemented"}"""
