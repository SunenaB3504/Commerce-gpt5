from services.api.utils.mcq_store import get_mcqs, get_mcq_by_id


def test_mcq_ingest_and_lookup():
    items = get_mcqs('economics', '1')
    assert isinstance(items, list) and len(items) >= 2
    item = get_mcq_by_id('economics', '1', 'eco1-m-001')
    assert item is not None
    assert item.get('answerIndex') == 0
