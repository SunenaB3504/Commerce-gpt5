from fastapi.testclient import TestClient
from services.api.main import app


def test_mcq_validate_uses_store():
    client = TestClient(app)
    payload = {
        "questionId": "eco1-m-001",
        "selectedIndex": 0,
        "subject": "economics",
        "chapter": "1"
    }
    r = client.post("/mcq/validate", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["result"] == "correct"
    assert data["correctIndex"] == 0
    assert isinstance(data.get("citations"), list)
