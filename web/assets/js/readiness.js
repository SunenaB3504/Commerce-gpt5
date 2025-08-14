import { API_BASE, ADMIN_TOKEN } from './config.js?v=5';

async function getJson(path) {
  const url1 = `${API_BASE}${path}`;
  try {
    const r = await fetch(url1);
    return r.ok ? r.json() : Promise.reject(await r.text());
  } catch (e) {
    const r = await fetch(path);
    return r.ok ? r.json() : Promise.reject(await r.text());
  }
}

function pct(x) { return (x * 100).toFixed(1) + '%'; }

async function loadSummary() {
  const el = document.getElementById('evSummary');
  const files = document.getElementById('evFiles');
  el.textContent = 'Loading...';
  try {
    const s = await getJson('/eval/summary');
    el.innerHTML = `<div class='grid grid-cols-3 gap-3'>
      <div class='p-3 rounded bg-gray-50 text-center'><div class='text-xs text-gray-500'>Questions</div><div class='text-lg font-semibold'>${s.total_questions}</div></div>
      <div class='p-3 rounded bg-gray-50 text-center'><div class='text-xs text-gray-500'>Hit@k</div><div class='text-lg font-semibold'>${pct(s.hit_rate)}</div></div>
      <div class='p-3 rounded bg-gray-50 text-center'><div class='text-xs text-gray-500'>Citations</div><div class='text-lg font-semibold'>${pct(s.citation_rate)}</div></div>
    </div>`;
    files.innerHTML = (s.files || []).map(f => `<div>• ${f.file} — ${JSON.stringify(f.summary)}</div>`).join('');
  } catch (e) {
    el.textContent = 'Failed to load summary';
  }
}

async function runEval() {
  const btn = document.getElementById('btnRunEval');
  const status = document.getElementById('runStatus');
  btn.disabled = true; status.textContent = 'Running...';
  try {
    const r = await fetch(`${API_BASE}/eval/run`, {method:'POST', headers: ADMIN_TOKEN ? {'x-admin-token': ADMIN_TOKEN}: {}});
    if(!r.ok) throw new Error(await r.text());
    const data = await r.json();
    status.textContent = `Completed: ${data.run.count} questions`;
    await loadSummary();
  } catch(e){
    status.textContent = 'Eval failed';
  } finally {
    btn.disabled = false;
  }
}

function renderThresholdInfo(cfg){
  const el = document.getElementById('thresholdInfo');
  if(!cfg){ el.textContent = 'Loading thresholds...'; return; }
  el.innerHTML = `<div class='grid grid-cols-2 gap-3'>
    <div class='p-2 bg-gray-50 rounded'><div class='text-xs text-gray-500'>Partial min</div><div class='font-semibold'>${cfg.partial_min}</div></div>
    <div class='p-2 bg-gray-50 rounded'><div class='text-xs text-gray-500'>Correct min</div><div class='font-semibold'>${cfg.correct_min}</div></div>
  </div>`;
}

async function fetchThresholds(){
  try {
    const r = await fetch(`${API_BASE}/admin/validate/thresholds`, {headers: ADMIN_TOKEN ? {'x-admin-token': ADMIN_TOKEN} : {}});
    if(!r.ok) throw new Error(await r.text());
    const data = await r.json();
    renderThresholdInfo(data);
  } catch(e){
    renderThresholdInfo(null);
  }
}

let _lastSuggestions = null;
async function requestSuggestions(){
  const el = document.getElementById('suggestions');
  el.textContent = 'Computing suggestions...';
  try {
    // For now, suggestions require client-provided rows; placeholder empty list.
    const payload = {rows: []};
    const r = await fetch(`${API_BASE}/admin/calibration/short-answer`, {method:'POST', headers:{'Content-Type':'application/json', ...(ADMIN_TOKEN?{'x-admin-token':ADMIN_TOKEN}:{})}, body: JSON.stringify(payload)});
    if(!r.ok) throw new Error(await r.text());
    const data = await r.json();
    _lastSuggestions = data.suggestions;
    el.innerHTML = `<div class='mb-2'>Suggested partial_min: <code>${data.suggestions.partial_min_suggested}</code>, correct_min: <code>${data.suggestions.correct_min_suggested}</code></div><pre class='bg-gray-50 p-2 rounded text-xs overflow-x-auto'>${JSON.stringify(data.suggestions.stats, null, 2)}</pre>`;
    document.getElementById('btnApply').disabled = false;
  } catch(e){
    el.textContent = 'Failed to compute suggestions (need scored rows).';
  }
}

async function applySuggestions(){
  if(!_lastSuggestions) return;
  const btn = document.getElementById('btnApply');
  btn.disabled = true;
  try {
    const payload = {partial_min: _lastSuggestions.partial_min_suggested, correct_min: _lastSuggestions.correct_min_suggested};
    const r = await fetch(`${API_BASE}/admin/validate/thresholds`, {method:'POST', headers:{'Content-Type':'application/json', ...(ADMIN_TOKEN?{'x-admin-token':ADMIN_TOKEN}:{})}, body: JSON.stringify(payload)});
    if(!r.ok) throw new Error(await r.text());
    await fetchThresholds();
  } catch(e){
    // ignore
  } finally {
    btn.disabled = false;
  }
}

document.getElementById('btnRunEval').addEventListener('click', runEval);
document.getElementById('btnRefresh').addEventListener('click', loadSummary);
document.getElementById('btnSuggest').addEventListener('click', requestSuggestions);
document.getElementById('btnApply').addEventListener('click', applySuggestions);

loadSummary();
fetchThresholds();
