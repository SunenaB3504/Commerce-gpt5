import json
from services.api.utils.chunker import chunk_pages
from services.api.utils.indexer import DiskIndex


def test_chunker_basic():
    pages = [(1, "alpha beta gamma"), (2, "delta epsilon zeta")]
    chunks = chunk_pages(pages, chunk_size=20, chunk_overlap=5, subject="Test", chapter="1")
    assert chunks, "Expected non-empty chunks"
    # Check metadata and page spans set
    for c in chunks:
        assert c.metadata.get("subject") == "Test"
        assert c.metadata.get("chapter") == "1"
        assert c.page_start >= 1 and c.page_end >= c.page_start


essay = """
Deindustrialisation had a two-fold motive: to promote British industries and to transform India into a supplier of raw materials. The colonial policies resulted in decline of handicrafts and rise of imports from Britain.
""".strip()


def test_retrieval_bm25_fallback(tmp_path):
    idx = DiskIndex(base_dir=str(tmp_path / "indexes"))
    # Build two simple chunks
    from services.api.utils.chunker import Chunk
    c1 = Chunk(id="1", text=essay, page_start=5, page_end=5, metadata={"page_start": 5, "page_end": 5})
    c2 = Chunk(id="2", text="Unrelated text about agriculture.", page_start=1, page_end=1, metadata={"page_start": 1, "page_end": 1})
    idx.upsert([c1, c2], subject="Economics", chapter="1")
    res = idx.query(subject="Economics", chapter="1", query="two-fold motive behind the deindustrialisation", k=2)
    hits = res.get("results", [])
    assert hits, "Expected non-empty results"
    assert "two-fold" in hits[0]["text"] or "two-fold" in hits[0]["text"].lower()
