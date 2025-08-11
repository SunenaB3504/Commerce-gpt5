from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from .chunker import Chunk

_MODEL_CACHE: Dict[str, Any] = {}


class DiskIndex:
    """Lightweight wrapper around Chroma persistent client per subject/chapter."""

    def __init__(self, base_dir: str = "indexes") -> None:
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _client(self, namespace: str):
        persist_dir = self.base / namespace
        persist_dir.mkdir(parents=True, exist_ok=True)
        try:
            import chromadb  # type: ignore
        except Exception as e:
            raise RuntimeError("chromadb_unavailable") from e
        client = chromadb.PersistentClient(path=str(persist_dir))
        return client

    def _collection(self, client, name: str, model: str = "all-MiniLM-L6-v2"):
        try:
            from chromadb.utils import embedding_functions  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "chromadb embedding_functions missing. Ensure chromadb is installed."
            ) from e
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)
        return client.get_or_create_collection(name=name, embedding_function=ef)

    def _ns(self, subject: Optional[str], chapter: Optional[str]) -> str:
        s = (subject or "general").replace(" ", "_")
        c = (chapter or "all").replace(" ", "_")
        return f"{s}-ch{c}"

    # --- Simple fallback (pure-Python JSON + sentence-transformers) ---
    def _ns_dir(self, namespace: str) -> Path:
        d = self.base / namespace
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _get_st_model(self, model: str):
        # Retained for Chroma path; not used in pure-Python fallback
        if model in _MODEL_CACHE:
            return _MODEL_CACHE[model]
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as e:
            raise RuntimeError("sentence-transformers not available") from e
        m = SentenceTransformer(model)
        _MODEL_CACHE[model] = m
        return m

    def _simple_upsert(self, namespace: str, chunks: List[Chunk], model: str) -> Dict[str, Any]:
        ns_dir = self._ns_dir(namespace)
        items_path = ns_dir / "items.json"

        # Load existing
        if items_path.exists():
            with items_path.open("r", encoding="utf-8") as f:
                try:
                    items = json.load(f)
                except Exception:
                    items = []
        else:
            items = []

        # Filter new by id uniqueness
        existing_ids = {it.get("id") for it in items if isinstance(it, dict)}
        new_chunks = [c for c in chunks if c.id not in existing_ids]
        if not new_chunks:
            return {"namespace": namespace, "count": len(items)}

        new_items = items + [
            {"id": c.id, "text": c.text, "metadata": c.metadata}
            for c in new_chunks
        ]

        with items_path.open("w", encoding="utf-8") as f:
            json.dump(new_items, f, ensure_ascii=False)

        return {"namespace": namespace, "count": len(new_items)}

    def _simple_query(self, namespace: str, query: str, k: int, model: str) -> Dict[str, Any]:
        ns_dir = self._ns_dir(namespace)
        items_path = ns_dir / "items.json"
        if not items_path.exists():
            return {"namespace": namespace, "results": []}

        with items_path.open("r", encoding="utf-8") as f:
            try:
                items = json.load(f)
            except Exception:
                items = []

        if not isinstance(items, list) or not items:
            return {"namespace": namespace, "results": []}

        texts = [it.get("text", "") for it in items]
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
            import math
            # Fit vectorizer on corpus
            vec = TfidfVectorizer(max_features=4096)
            X = vec.fit_transform(texts)  # shape: (n_docs, n_terms)
            q = vec.transform([query])    # shape: (1, n_terms)
            # Compute cosine similarity: (X * q.T).toarray().ravel()
            sims = (X @ q.T).toarray().ravel()
            # Build top-k indices
            top_idx = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:k]
            out = []
            for i in top_idx:
                it = items[i]
                score = float(sims[i])
                # Distance as 1 - normalized score best-effort
                out.append({
                    "text": it.get("text", ""),
                    "metadata": it.get("metadata", {}),
                    "distance": float(1.0 - score),
                })
            return {"namespace": namespace, "results": out}
        except Exception:
            # Fallback to token-overlap similarity
            def tok(s: str) -> set:
                return set(t.lower() for t in s.split())
            qset = tok(query)
            scored = []
            for i, t in enumerate(texts):
                s = tok(t)
                inter = len(qset & s)
                uni = len(qset | s) or 1
                jacc = inter / uni
                scored.append((jacc, i))
            scored.sort(key=lambda x: x[0], reverse=True)
            out = []
            for score, i in scored[:k]:
                it = items[i]
                out.append({
                    "text": it.get("text", ""),
                    "metadata": it.get("metadata", {}),
                    "distance": float(1.0 - score),
                })
            return {"namespace": namespace, "results": out}

    def upsert(self, chunks: List[Chunk], *, subject: Optional[str], chapter: Optional[str], model: str = "all-MiniLM-L6-v2") -> Dict[str, Any]:
        ns = self._ns(subject, chapter)
        try:
            client = self._client(ns)
            coll = self._collection(client, name="chunks", model=model)
            ids = [c.id for c in chunks]
            texts = [c.text for c in chunks]
            metadatas = [c.metadata for c in chunks]
            if not ids:
                return {"namespace": ns, "count": 0}
            coll.upsert(ids=ids, documents=texts, metadatas=metadatas)
            # Chroma doesn't return count; assume added all
            return {"namespace": ns, "count": len(coll.get()["ids"]) if hasattr(coll, "get") else len(ids)}
        except RuntimeError as e:
            # Fallback if chroma unavailable
            if str(e) == "chromadb_unavailable":
                return self._simple_upsert(ns, chunks, model)
            raise

    def query(self, *, subject: Optional[str], chapter: Optional[str], query: str, k: int = 5, model: str = "all-MiniLM-L6-v2") -> Dict[str, Any]:
        ns = self._ns(subject, chapter)
        try:
            client = self._client(ns)
            coll = self._collection(client, name="chunks", model=model)
            res = coll.query(query_texts=[query], n_results=k, include=["documents", "metadatas", "distances"])
            out = []
            if res and res.get("documents"):
                docs = res["documents"][0]
                metas = res.get("metadatas", [[{}]])[0]
                dists = res.get("distances", [[None]])[0]
                for t, m, d in zip(docs, metas, dists):
                    item = {"text": t, "metadata": m}
                    if d is not None:
                        item["distance"] = d
                    out.append(item)
            return {"namespace": ns, "results": out}
        except RuntimeError as e:
            if str(e) == "chromadb_unavailable":
                return self._simple_query(ns, query, k, model)
            raise
