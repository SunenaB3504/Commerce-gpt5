from fastapi.testclient import TestClient
from services.api.main import app

client = TestClient(app)


def test_mcq_get_by_id():
    r = client.post('/mcq/get', json={"subject": "economics", "chapter": "1", "questionId": "eco1-m-001"})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "eco1-m-001"
    assert isinstance(data.get("options"), list) and len(data["options"]) == 4


def test_mcq_validate_correct_and_incorrect():
    # Correct
    rc = client.post('/mcq/validate', json={
        "subject": "economics", "chapter": "1", "questionId": "eco1-m-001", "selectedIndex": 0
    })
    assert rc.status_code == 200
    dc = rc.json()
    assert dc["result"] == "correct" and dc["correctIndex"] == 0

    # Incorrect
    ri = client.post('/mcq/validate', json={
        "subject": "economics", "chapter": "1", "questionId": "eco1-m-001", "selectedIndex": 2
    })
    assert ri.status_code == 200
    di = ri.json()
    assert di["result"] == "incorrect" and di["correctIndex"] == 0
