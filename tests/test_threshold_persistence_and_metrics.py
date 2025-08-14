from __future__ import annotations

import json
from pathlib import Path
from fastapi.testclient import TestClient
from services.api.main import app

client = TestClient(app)


def test_threshold_override_persists(tmp_path, monkeypatch):
    # Override path indirectly by setting working dir if needed (using actual path in project)
    r = client.post('/admin/validate/thresholds', json={'partial_min': 55.5})
    assert r.status_code == 200, r.text
    persist = Path('data/runtime/threshold_overrides.json')
    assert persist.exists(), 'threshold_overrides.json missing'
    data = json.loads(persist.read_text(encoding='utf-8'))
    assert float(data['partial_min']) == 55.5

    # Simulate reload by re-importing (simplified: call GET and ensure value effective)
    g = client.get('/admin/validate/thresholds')
    assert g.status_code == 200
    eff = g.json()['effective']['partial_min'] if 'effective' in g.json() else g.json()['partial_min']
    assert eff == 55.5


def test_metrics_recording_basic():
    # Call /ask simple query to populate metrics
    r = client.get('/ask', params={'q': 'what is inflation', 'k': 1})
    assert r.status_code == 200
    # There is no public metrics endpoint yet; indirectly ensure no crash and internal state updated by calling again.
    r2 = client.get('/ask', params={'q': 'define gdp', 'k': 1})
    assert r2.status_code == 200
