import { API_BASE } from './config.js?v=5';

const form = document.getElementById('mcqForm');
const statusEl = document.getElementById('mcqStatus');
const resultEl = document.getElementById('mcqResult');
const loadBtn = document.getElementById('loadMcqBtn');
const loadStatus = document.getElementById('loadStatus');
const mcqText = document.getElementById('mcqText');
const mcqOptions = document.getElementById('mcqOptions');

async function postValidate(payload) {
  const url1 = `${API_BASE}/mcq/validate`;
  try {
    const r = await fetch(url1, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    return r;
  } catch (e) {
    return fetch('/mcq/validate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  }
}

async function postGet(payload) {
  const url1 = `${API_BASE}/mcq/get`;
  try {
    const r = await fetch(url1, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    return r;
  } catch (e) {
    return fetch('/mcq/get', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  }
}

function renderOptions(options) {
  mcqOptions.innerHTML = '';
  if (!Array.isArray(options) || !options.length) {
    mcqOptions.innerHTML = '<div class="text-xs text-gray-600">No options available.</div>';
    return;
  }
  options.forEach((opt, i) => {
    const id = `opt_${i}`;
    const label = document.createElement('label');
    label.className = 'flex items-center gap-2 text-sm';
    label.innerHTML = `<input type="radio" name="opt" value="${i}" ${i===0?'checked':''}/> <span><span class="font-medium">${String.fromCharCode(65+i)}.</span> ${opt}</span>`;
    mcqOptions.appendChild(label);
  });
}

loadBtn?.addEventListener('click', async () => {
  const subject = document.getElementById('mcqSubject').value || '';
  const chapter = document.getElementById('mcqChapter').value || '';
  const questionId = document.getElementById('mcqId').value || '';
  loadStatus.textContent = 'Loading...';
  mcqText.textContent = '';
  mcqOptions.innerHTML = '';
  resultEl.innerHTML = '';
  statusEl.textContent = '';
  try {
    const res = await postGet({ subject, chapter, questionId });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    mcqText.textContent = data.question || 'Not found';
    renderOptions(data.options || []);
    loadStatus.textContent = data.question === 'Not found' ? 'Not found' : 'Loaded';
  } catch (e) {
    loadStatus.textContent = 'Failed to load';
  }
});

form?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const subject = document.getElementById('mcqSubject').value || '';
  const chapter = document.getElementById('mcqChapter').value || '';
  const questionId = document.getElementById('mcqId').value || '';
  const selectedIndex = Number(new FormData(form).get('opt') || 0);

  statusEl.textContent = 'Validating...';
  resultEl.innerHTML = '';
  try {
    const res = await postValidate({ subject, chapter, questionId, selectedIndex });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    const good = data.result === 'correct';
    statusEl.textContent = good ? 'Correct ✅' : 'Incorrect ❌';
    const ex = data.explanation ? `<div class="mt-2"><span class="font-medium">Explanation:</span> ${data.explanation}</div>` : '';
    const cites = (data.citations || []).length ? `<div class="mt-2 text-xs text-gray-600">Sources: ${(data.citations || []).map(c => `${c.filename || 'Document'} p${c.page_start}`).join(', ')}</div>` : '';
    resultEl.innerHTML = ex + cites;
  } catch (err) {
    statusEl.textContent = 'Failed to validate';
    resultEl.textContent = String(err);
  }
});
