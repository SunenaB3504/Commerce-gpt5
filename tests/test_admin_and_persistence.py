from __future__ import annotations

import os
import json
from pathlib import Path
from fastapi.testclient import TestClient
from services.api.main import app

client = TestClient(app)


def _admin_headers():
    token = os.environ.get('ADMIN_TOKEN')
    if token:
        return {'x-admin-token': token}
    return {}


def test_session_persistence_creates_file(tmp_path, monkeypatch):
    # point runtime dir to tmp
    runtime_dir = tmp_path / 'runtime'
    monkeypatch.setenv('PYTHONHASHSEED', '0')
    # Start a session
    r = client.post('/practice/start', json={'subject':'Economics','chapter':'1','total':2,'mcq':1,'short':1})
    assert r.status_code == 200, r.text
    data = r.json()
    sid = data['sessionId']
    # Submit a dummy answer depending on type
    if data['type'] == 'mcq':
        sub = client.post('/practice/submit', json={'sessionId': sid, 'type':'mcq','questionId': data['questionId'],'selectedIndex':0})
    else:
        sub = client.post('/practice/submit', json={'sessionId': sid, 'type':'short','answer':'test'})
    assert sub.status_code in (200,400)
    # Persistence file should exist
    persist = Path('data/runtime/practice_sessions.json')
    assert persist.exists(), 'persistence file not created'


def test_threshold_update_round_trip():
    # Get current thresholds
    r1 = client.get('/admin/validate/thresholds', headers=_admin_headers())
    assert r1.status_code == 200, r1.text
    base = r1.json()
    new_partial = float(base['partial_min']) + 1.0
    payload = {'partial_min': new_partial}
    r2 = client.post('/admin/validate/thresholds', json=payload, headers=_admin_headers())
    assert r2.status_code == 200, r2.text
    eff = r2.json()['effective']
    assert eff['partial_min'] == new_partial


def test_eval_run_endpoint(monkeypatch):
    # Monkeypatch subprocess to avoid running full eval
    import services.api.routes.eval as eval_module
    class DummyCP:
        returncode = 0
        stdout = ''
        stderr = ''
    def fake_run(cmd, capture_output, text, timeout):
        # write minimal results file referenced in command
        out_index = cmd.index('--out') + 1
        out_path = Path(cmd[out_index])
        out_path.write_text(json.dumps({'summary': {'count':0,'hit_at_k':0,'answers':0,'citations':0}}, indent=2), encoding='utf-8')
        return DummyCP()
    monkeypatch.setattr(eval_module.subprocess, 'run', fake_run)
    r = client.post('/eval/run', headers=_admin_headers())
    assert r.status_code == 200, r.text
    js = r.json()
    assert 'run' in js and 'file' in js
