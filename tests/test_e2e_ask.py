from typing import Any

import json
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.utils.chunker import Chunk
from services.api.utils.indexer import DiskIndex
import services.api.routes.ask as ask_route


def seed_index(tmp_path) -> str:
    base_dir = tmp_path / "indexes"
    idx = DiskIndex(base_dir=str(base_dir))
    # Seed: one relevant, one irrelevant, one exercise-like noise
    essay = (
        "De-industrialisation had a two-fold motive: to promote British industries and to transform "
        "India into a supplier of raw materials and a market for British goods."
    )
    c1 = Chunk(id="1", text=essay, page_start=12, page_end=13, metadata={"page_start": 12, "page_end": 13, "filename": "test.pdf"})
    c2 = Chunk(id="2", text="Unrelated text about agriculture only.", page_start=1, page_end=1, metadata={"page_start": 1, "page_end": 1, "filename": "test.pdf"})
    c3 = Chunk(id="3", text="Work these out: What was the two-fold motive? Name three industries.", page_start=13, page_end=13, metadata={"page_start": 13, "page_end": 13, "filename": "test.pdf"})
    idx.upsert([c1, c2, c3], subject="Economics", chapter="1")
    # Return namespace used by routes
    return "Economics-ch1"


def patch_disk_index_to_tmp(monkeypatch: Any, tmp_path) -> None:
    ns_base = tmp_path / "indexes"

    class FixedDiskIndex(DiskIndex):
        def __init__(self, base_dir: str = str(ns_base)) -> None:
            super().__init__(base_dir=base_dir)

    # Patch the reference used inside ask route
    monkeypatch.setattr(ask_route, "DiskIndex", FixedDiskIndex)


def test_ask_e2e_answer_and_citations(monkeypatch, tmp_path):
    seed_index(tmp_path)
    patch_disk_index_to_tmp(monkeypatch, tmp_path)
    client = TestClient(app)

    params = {
        "q": "two-fold motive behind the deindustrialisation",
        "subject": "Economics",
        "chapter": "1",
        "k": 5,
        "answer_synthesis": True,
    }
    r = client.get("/ask", params=params)
    assert r.status_code == 200, r.text
    data = r.json()
    # Namespace should match
    assert data.get("namespace") == "Economics-ch1"
    # Should have results and an answer
    assert data.get("results"), "Expected non-empty results"
    ans = data.get("answer") or ""
    # Answer must reference raw materials and market for British goods
    assert "raw materials" in ans.lower()
    assert "market for british goods" in ans.lower()
    # Should include at least one citation
    cites = data.get("citations") or []
    assert len(cites) >= 1
    # Ensure noisy exercise/question text is filtered out of the final answer
    assert "work these out" not in ans.lower()
    assert not ans.strip().endswith("?")


def test_ask_stream_e2e(monkeypatch, tmp_path):
    seed_index(tmp_path)
    patch_disk_index_to_tmp(monkeypatch, tmp_path)
    client = TestClient(app)
    params = {
        "q": "two-fold motive behind the deindustrialisation",
        "subject": "Economics",
        "chapter": "1",
        "k": 5,
    }
    with client.stream("GET", "/ask/stream", params=params) as resp:
        assert resp.status_code == 200
        # Collect a small portion of the stream to validate presence of answer event
        text = "".join([chunk.decode("utf-8") if isinstance(chunk, (bytes, bytearray)) else chunk for chunk in resp.iter_lines()][:10])
        assert "\"type\": \"answer\"" in text or "\"type\":\"answer\"" in text
