import { API_BASE } from './config.js?v=5';

const form = document.getElementById('mcqForm');
const statusEl = document.getElementById('mcqStatus');
const resultEl = document.getElementById('mcqResult');
const loadBtn = document.getElementById('loadMcqBtn');
const loadStatus = document.getElementById('loadStatus');
const mcqText = document.getElementById('mcqText');
const mcqOptions = document.getElementById('mcqOptions');

// Practice Session selectors
const psStartBtn = document.getElementById('psStart');
const psStatus = document.getElementById('psStatus');
const psCard = document.getElementById('psCard');
const psProgress = document.getElementById('psProgress');
const psQuestion = document.getElementById('psQuestion');
const psOptions = document.getElementById('psOptions');
const psShort = document.getElementById('psShort');
const psSubmit = document.getElementById('psSubmit');
const psNext = document.getElementById('psNext');
const psFeedback = document.getElementById('psFeedback');
// Voice controls
const psVoiceToggle = document.getElementById('psVoiceToggle');
const psSpeak = document.getElementById('psSpeak');
const psListen = document.getElementById('psListen');
const psVoiceStatus = document.getElementById('psVoiceStatus');
const psTranscript = document.getElementById('psTranscript');
const psTranscriptUse = document.getElementById('psTranscriptUse');
let psState = { sessionId: null, index: 0, total: 0, type: null, questionId: null };

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

async function postJson(path, body) {
  const url1 = `${API_BASE}${path}`;
  try {
    return await fetch(url1, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  } catch (e) {
    return await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  }
}

function renderPracticeQuestion(data) {
  psState.sessionId = data.sessionId; psState.index = data.index; psState.total = data.total; psState.type = data.type; psState.questionId = data.questionId || null;
  psCard.classList.remove('hidden');
  psProgress.textContent = `Question ${data.index + 1} of ${data.total} (${data.type === 'mcq' ? 'MCQ' : 'Short Answer'})`;
  psQuestion.textContent = data.question;
  psOptions.innerHTML = '';
  psShort.innerHTML = '';
  if (psFeedback) psFeedback.innerHTML = '';
  psNext.disabled = true;
  if (psTranscriptUse) psTranscriptUse.disabled = (data.type !== 'short');
  if (data.type === 'mcq') {
    (data.options || []).forEach((opt, i) => {
      const label = document.createElement('label');
      label.className = 'flex items-center gap-2 text-sm';
      label.innerHTML = `<input type="radio" name="psopt" value="${i}" ${i===0?'checked':''}/> <span><span class="font-medium">${String.fromCharCode(65+i)}.</span> ${opt}</span>`;
      psOptions.appendChild(label);
    });
  } else {
    const ta = document.createElement('textarea');
    ta.id = 'psAnswer';
    ta.className = 'w-full border rounded p-2 text-sm';
    ta.rows = 4;
    ta.placeholder = 'Type your answer...';
    psShort.appendChild(ta);
    // If transcript already has text, offer it as default
    if (psTranscript && psTranscript.value && !ta.value) {
      ta.value = psTranscript.value.trim();
    }
  }
}

psStartBtn?.addEventListener('click', async () => {
  const subject = document.getElementById('psSubject').value || '';
  const chapter = document.getElementById('psChapter').value || '';
  const mixVal = (document.getElementById('psMix').value || '3/3').split('/');
  const mcq = parseInt(mixVal[0] || '3', 10);
  const short = parseInt(mixVal[1] || '3', 10);
  psStatus.textContent = 'Starting...';
  try {
    const res = await postJson('/practice/start', { subject, chapter, mcq, short, total: mcq + short });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderPracticeQuestion(data);
    psStatus.textContent = 'Session started';
  } catch (e) {
    psStatus.textContent = 'Failed to start session';
  }
});

psSubmit?.addEventListener('click', async () => {
  if (!psState.sessionId) return;
  psStatus.textContent = 'Submitting...';
  psFeedback.innerHTML = '';
  try {
    let payload = { sessionId: psState.sessionId, type: psState.type, questionId: psState.questionId };
    if (psState.type === 'mcq') {
  const sel = document.querySelector('input[name="psopt"]:checked');
  payload.selectedIndex = sel ? Number(sel.value) : 0;
    } else {
      payload.answer = (document.getElementById('psAnswer')?.value || '').trim();
    }
    const res = await postJson('/practice/submit', payload);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    const sub = data.submission || {};
    if (psState.type === 'mcq') {
      const good = sub.result === 'correct';
      psFeedback.innerHTML = `<div>${good ? 'Correct ✅' : 'Incorrect ❌'}</div>` +
        (sub.explanation ? `<div class='mt-2'><span class='font-medium'>Explanation:</span> ${sub.explanation}</div>` : '');
    } else {
      psFeedback.innerHTML = `<div>Result: <span class='font-medium'>${sub.result}</span> (Score: ${sub.score})</div>` +
        (Array.isArray(sub.feedback) && sub.feedback.length ? `<ul class='mt-2 list-disc pl-6 text-sm text-gray-700'>${sub.feedback.map(f=>`<li>${f}</li>`).join('')}</ul>` : '');
    }
    psNext.disabled = !data.hasNext;
    psStatus.textContent = 'Submitted';
  } catch (e) {
    psStatus.textContent = 'Submit failed';
  }
});

psNext?.addEventListener('click', async () => {
  if (!psState.sessionId) return;
  psStatus.textContent = 'Loading next...';
  try {
    const res = await postJson('/practice/next', { sessionId: psState.sessionId });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderPracticeQuestion(data);
    psStatus.textContent = '';
  } catch (e) {
    psStatus.textContent = 'No more questions';
  }
});

// --- Voice: TTS & STT (beta) ---
function ttsSpeak(text) {
  try {
    if (!('speechSynthesis' in window)) return;
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.0; u.pitch = 1.0;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  } catch {}
}

function readCurrentQuestion() {
  const parts = [];
  parts.push(psQuestion.textContent || '');
  if (psState.type === 'mcq') {
    const radios = psOptions.querySelectorAll('input[name="psopt"]');
    radios.forEach((r, i) => {
      const label = r.closest('label');
      const txt = label ? label.textContent : `Option ${i+1}`;
      parts.push(txt || '');
    });
  }
  ttsSpeak(parts.filter(Boolean).join('. '));
}

let recognition = null;
let silenceTimer = null;
const SILENCE_MS = 5000;
function getRecognizer() {
  if (recognition) return recognition;
  const C = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!C) {
    if (psVoiceStatus) psVoiceStatus.textContent = 'Speech recognition not supported in this browser';
    return null;
  }
  recognition = new C();
  recognition.lang = 'en-US';
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;
  recognition.onstart = () => { if (psVoiceStatus) psVoiceStatus.textContent = 'Listening... allow microphone access if prompted'; if (psTranscript) psTranscript.value = ''; };
  recognition.onend = () => { if (psVoiceStatus) psVoiceStatus.textContent = 'Stopped'; };
  recognition.onerror = (e) => { if (psVoiceStatus) psVoiceStatus.textContent = `Error: ${e.error}`; };
  recognition.onresult = (e) => {
    // Build transcript from all results; last result may be final
    let text = '';
    for (let i = 0; i < e.results.length; i++) {
      text += (e.results[i][0]?.transcript || '') + ' ';
    }
    text = text.trim();
    if (psTranscript) psTranscript.value = text;
    if (psTranscript) {
      const wc = text ? text.split(/\s+/).filter(Boolean).length : 0;
      if (psVoiceStatus) psVoiceStatus.textContent = `Listening... (${wc} words)`;
    }
    if (silenceTimer) clearTimeout(silenceTimer);
    silenceTimer = setTimeout(() => {
      try { recognition.stop(); if (psVoiceStatus) psVoiceStatus.textContent = 'Auto-stopped after silence'; } catch {}
    }, SILENCE_MS);
    if (e.results[e.results.length - 1].isFinal) {
      const cmd = text.toLowerCase();
      if (cmd) handleVoiceCommand(cmd);
    }
  };
  return recognition;
}

function handleVoiceCommand(cmd) {
  const say = (m) => ttsSpeak(m);
  if (cmd.includes('repeat') || cmd.includes('again')) {
    readCurrentQuestion();
    return;
  }
  if (cmd.includes('next') || cmd.includes('skip')) {
    psNext?.click();
    say('Next question');
    return;
  }
  if (psState.type === 'mcq') {
    const map = { 'a': 0, 'b': 1, 'c': 2, 'd': 3 };
    for (const [k, v] of Object.entries(map)) {
      if (cmd.includes(`option ${k}`) || cmd === k) {
        const el = psOptions.querySelector(`input[name="psopt"][value="${v}"]`);
        if (el) { el.checked = true; say(`Selected option ${k.toUpperCase()}`); }
        return;
      }
    }
    if (cmd.includes('submit')) { psSubmit?.click(); return; }
  } else {
    // For short answers, simple dictation append
    if (cmd.startsWith('answer')) {
      const text = cmd.replace('answer', '').trim();
      const ta = document.getElementById('psAnswer');
      if (ta) { ta.value = (ta.value ? ta.value + ' ' : '') + text; say('Added to answer'); }
      return;
    }
    if (cmd.includes('submit')) { psSubmit?.click(); return; }
  }
}

psSpeak?.addEventListener('click', () => {
  if (!psVoiceToggle?.checked) return;
  readCurrentQuestion();
});

psListen?.addEventListener('click', () => {
  if (!psVoiceToggle?.checked) return;
  const r = getRecognizer();
  if (r) r.start();
});

psTranscriptUse?.addEventListener('click', () => {
  if (psState.type !== 'short') {
    if (psVoiceStatus) psVoiceStatus.textContent = 'Use as answer is available for short-answer questions only';
    return;
  }
  const ta = document.getElementById('psAnswer');
  if (ta && psTranscript && psTranscript.value) {
    ta.value = psTranscript.value.trim();
    ta.focus();
    if (psVoiceStatus) psVoiceStatus.textContent = 'Copied transcript to answer';
  } else {
    if (psVoiceStatus) psVoiceStatus.textContent = 'Nothing to copy';
  }
});
