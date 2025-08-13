from fastapi.testclient import TestClient
from services.api.main import app


def test_teach_outline_sections():
    client = TestClient(app)
    payload = {"subject": "Economics", "chapter": "1", "topics": ["overview"], "k": 6, "retriever": "bm25"}
    r = client.post("/teach", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    outline = data.get("outline", [])
    assert isinstance(outline, list) and len(outline) >= 3
    ids = [s.get("sectionId") for s in outline]
    for expected in ["overview", "key-terms", "short-answers"]:
        assert expected in ids
    # Check overview has citations array
    ov = next(s for s in outline if s.get("sectionId") == "overview")
    assert isinstance(ov.get("citations"), list)


def test_mcq_validate_stub_200():
    client = TestClient(app)
    payload = {
        "questionId": "eco1-m-001",
        "question": "What is X?",
        "options": ["A", "B", "C", "D"],
        "correctIndex": 2,
        "selectedIndex": 1,
        "subject": "Economics",
        "chapter": "1",
    }
    r = client.post("/mcq/validate", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert set(["result", "correctIndex", "explanation", "citations"]).issubset(data.keys())


def test_teach_glossary_and_depth_caps():
    client = TestClient(app)
    # Request deep vs basic to observe cap differences
    payload_deep = {"subject": "Economics", "chapter": "1", "topics": ["overview"], "k": 6, "depth": "deep", "retriever": "bm25"}
    payload_basic = {"subject": "Economics", "chapter": "1", "topics": ["overview"], "k": 6, "depth": "basic", "retriever": "bm25"}
    r1 = client.post("/teach", json=payload_deep)
    r2 = client.post("/teach", json=payload_basic)
    assert r1.status_code == 200 and r2.status_code == 200
    d1 = r1.json()
    d2 = r2.json()
    # Glossary should be present (may be empty but key exists)
    assert "glossary" in d1
    # Compare caps via outline lengths (overview bullets)
    ov1 = next((s for s in d1.get("outline", []) if s.get("sectionId") == "overview"), {})
    ov2 = next((s for s in d2.get("outline", []) if s.get("sectionId") == "overview"), {})
    # Deep should allow >= basic count when data available
    if isinstance(ov1.get("bullets"), list) and isinstance(ov2.get("bullets"), list):
        assert len(ov1.get("bullets")) >= len(ov2.get("bullets"))
