from services.api.utils.answerer import build_answer


def test_retirement_ways_list_format():
    # Simulate hits containing relevant lines
    passages = [
        {
            "text": (
                "Ways a partner may retire:\n"
                "1) With consent of all partners (mutual agreement)\n"
                "2) As per the partnership deed if it permits retirement\n"
                "3) In a partnership at will, by written notice to all partners\n"
            ),
            "metadata": {"page_start": 33, "page_end": 34, "filename": "leac103.pdf", "source_path": "uploads/x.pdf"},
        }
    ]
    out = build_answer("Ways a partner can retire from the firm", passages, mmr=False, max_passages=3, max_chars=500, filter_noise=True)
    ans = out.get("answer") or ""
    assert "•" in ans or "1)" in ans or "- " in ans, ans
    assert "consent" in ans.lower()
    assert "partnership deed" in ans.lower() or "deed" in ans.lower()
    assert "partnership at will" in ans.lower() or "written notice" in ans.lower()
