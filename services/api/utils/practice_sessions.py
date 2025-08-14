from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
import time
import uuid
import json
from pathlib import Path

from .mcq_store import get_mcqs
from .curated_qa import _combined_entries


@dataclass
class PracticeQuestion:
    qtype: str  # 'mcq' | 'short'
    id: str
    question: str
    options: Optional[List[str]] = None  # for mcq
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PracticeSession:
    session_id: str
    subject: str
    chapter: str
    created_at: float
    questions: List[PracticeQuestion]
    index: int = 0
    answers: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.questions)

    def current(self) -> Optional[PracticeQuestion]:
        if 0 <= self.index < len(self.questions):
            return self.questions[self.index]
        return None

    def next(self) -> Optional[PracticeQuestion]:
        self.index += 1
        return self.current()


_SESSIONS: Dict[str, PracticeSession] = {}

# Persistence configuration
_PERSIST_PATH = Path(__file__).resolve().parents[3] / "data" / "runtime" / "practice_sessions.json"
_PERSIST_PATH.parent.mkdir(parents=True, exist_ok=True)
_SESSION_TTL_SECONDS = 60 * 60 * 6  # 6 hours
_LAST_LOAD = 0.0


def _serialize_session(sess: PracticeSession) -> Dict[str, Any]:
    return {
        "session_id": sess.session_id,
        "subject": sess.subject,
        "chapter": sess.chapter,
        "created_at": sess.created_at,
        "index": sess.index,
        "answers": sess.answers,
        "questions": [
            {
                "qtype": q.qtype,
                "id": q.id,
                "question": q.question,
                "options": q.options,
                "meta": q.meta,
            } for q in sess.questions
        ],
    }


def _deserialize_session(d: Dict[str, Any]) -> Optional[PracticeSession]:
    try:
        questions = [PracticeQuestion(qtype=q.get("qtype"), id=q.get("id"), question=q.get("question"), options=q.get("options"), meta=q.get("meta") or {}) for q in d.get("questions", [])]
        return PracticeSession(
            session_id=d.get("session_id"),
            subject=d.get("subject"),
            chapter=d.get("chapter"),
            created_at=float(d.get("created_at")),
            questions=questions,
            index=int(d.get("index", 0)),
            answers=d.get("answers", []),
        )
    except Exception:
        return None


def _prune_and_persist() -> None:
    # Remove expired sessions then persist all
    now = time.time()
    expired = []
    for sid, sess in list(_SESSIONS.items()):
        if (now - sess.created_at) > _SESSION_TTL_SECONDS:
            expired.append(sid)
    for sid in expired:
        _SESSIONS.pop(sid, None)
    try:
        payload = {sid: _serialize_session(s) for sid, s in _SESSIONS.items()}
        _PERSIST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _lazy_load() -> None:
    global _LAST_LOAD
    if _SESSIONS or not _PERSIST_PATH.exists():
        return
    try:
        data = json.loads(_PERSIST_PATH.read_text(encoding="utf-8"))
        for sid, raw in data.items():
            sess = _deserialize_session(raw)
            if not sess:
                continue
            if (time.time() - sess.created_at) > _SESSION_TTL_SECONDS:
                continue
            _SESSIONS[sid] = sess
    except Exception:
        pass
    _LAST_LOAD = time.time()


def _gen_mcq_questions(subject: str, chapter: str, limit: int) -> List[PracticeQuestion]:
    out: List[PracticeQuestion] = []
    mcqs = get_mcqs(subject, chapter)
    for m in mcqs[:limit]:
        out.append(PracticeQuestion(
            qtype="mcq",
            id=m.get("id") or str(uuid.uuid4()),
            question=m.get("question") or "",
            options=m.get("options") or [],
            meta={"mcq_id": m.get("id")},
        ))
    return out


def _gen_short_questions(subject: str, chapter: str, limit: int) -> List[PracticeQuestion]:
    out: List[PracticeQuestion] = []
    # Use curated entries as short-answer prompts when available
    try:
        entries = [e for e in _combined_entries() if (
            (not subject or e.get("subject", "").strip().lower() == (subject or "").strip().lower()) and
            (not chapter or e.get("chapter", "").strip().lower() == (chapter or "").strip().lower())
        )]
    except Exception:
        entries = []
    for e in entries[:limit]:
        q = e.get("q") or ""
        if not q:
            continue
        out.append(PracticeQuestion(
            qtype="short",
            id=f"short:{hash(q)}",
            question=q,
        ))
    return out


def start_session(subject: str, chapter: str, total: int = 6, mix: Tuple[int, int] = (3, 3)) -> PracticeSession:
    _lazy_load()
    mcq_n, short_n = mix
    mcq_qs = _gen_mcq_questions(subject, chapter, mcq_n)
    short_qs = _gen_short_questions(subject, chapter, short_n)
    # If not enough curated short questions, fill with extra MCQs
    if len(short_qs) < short_n:
        extra = short_n - len(short_qs)
        mcq_qs.extend(_gen_mcq_questions(subject, chapter, extra))
    qs = mcq_qs + short_qs
    # Cap total
    qs = qs[:total]
    sid = str(uuid.uuid4())
    sess = PracticeSession(session_id=sid, subject=subject, chapter=chapter, created_at=time.time(), questions=qs)
    _SESSIONS[sid] = sess
    _prune_and_persist()
    return sess


def get_session(session_id: str) -> Optional[PracticeSession]:
    _lazy_load()
    sess = _SESSIONS.get(session_id)
    if not sess:
        return None
    if (time.time() - sess.created_at) > _SESSION_TTL_SECONDS:
        # Expired; remove and persist
        _SESSIONS.pop(session_id, None)
        _prune_and_persist()
        return None
    return sess


def record_answer(session: PracticeSession, question_id: str, payload: Dict[str, Any]) -> None:
    session.answers.append({
        "index": session.index,
        "question_id": question_id,
        "qtype": (session.current().qtype if session.current() else None),
        "answer": payload,
        "ts": time.time(),
    })
    _prune_and_persist()
