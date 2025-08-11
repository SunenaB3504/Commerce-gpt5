# Data schema

## Documents
- documents(id, subject, chapter, board, source_path, pages, version, uploaded_at)
- chunks(id, document_id, text, token_count, page_start, page_end, embedding)

## Q/A
- questions(id, subject, chapter, type, prompt, difficulty, answer_key, rubric, source_refs)
- attempts(id, user_id, question_id, response, score, feedback, created_at)

## Users (optional)
- users(id, role, prefs)

## Retention & privacy
- PDFs stored locally; purge on request.
- No PII collection by default.

## JSON shapes (for GitHub Pages hosting)
Manifest (web/data/index.json)
{
	"version": "v1",
	"generatedAt": "2025-08-11T00:00:00Z",
	"subjects": ["Economics", "Business Studies", "Accountancy"],
	"chapters": [
		{"subject": "Economics", "chapter": "1", "title": "Intro to Economics", "files": [
			{"url": "/data/subjects/Economics/chapters/1/chunks-001.json", "sha256": "...", "bytes": 524288, "purpose": "chunks"}
		]}
	]
}

Chunk file (chunks-001.json)
{
	"document": {"subject": "Economics", "chapter": "1", "source": "Economics_Ch1.pdf", "pages": [1, 12]},
	"chunks": [
		{"id": "eco1-0001", "text": "...", "pageStart": 1, "pageEnd": 2, "tokens": 512, "meta": {"topic": "Definition of Economics"}},
		{"id": "eco1-0002", "text": "...", "pageStart": 2, "pageEnd": 3, "tokens": 440, "meta": {"topic": "Scarcity"}}
	]
}

Public question bank (mcq.json)
[
	{"id": "eco1-m-001", "type": "MCQ", "question": "...", "options": ["A", "B", "C", "D"], "answer": 1, "explanation": "...", "source": {"chapter": 1, "pages": [5, 6]}},
	{"id": "eco1-m-002", "type": "MCQ", "question": "...", "options": ["A", "B", "C", "D"], "answer": 3, "explanation": "...", "source": {"chapter": 1, "pages": [7]}}
]

Note: Do not host full copyrighted chapter text publicly unless you have rights. Keep sensitive/raw text private or behind the backend.
