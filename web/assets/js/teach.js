import { API_BASE } from './config.js?v=5';
import { showToast, setBusy } from './ui.js';

const form = document.getElementById('teachForm');
const resultEl = document.getElementById('teachResult');
const copyBtn = document.getElementById('copyOutlineBtn');
const printBtn = document.getElementById('printBtn');

async function postTeach(payload, signal) {
  // Try configured API base first; on network/CORS failure, retry same-origin
  const url1 = `${API_BASE}/teach`;
  try {
    const res = await fetch(url1, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal
    });
    return res;
  } catch (e) {
    // Fallback to same-origin
    return fetch('/teach', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal
    });
  }
}

function renderSection(sec) {
  const wrap = document.createElement('section');
  wrap.className = 'bg-white rounded-xl shadow-sm ring-1 ring-gray-200 p-5 print-section';
  const h = document.createElement('h3');
  h.className = 'text-base font-semibold text-gray-800 mb-2';
  h.textContent = sec.title || sec.sectionId;
  wrap.appendChild(h);
  if (sec.pageAnchors && sec.pageAnchors.length) {
    const badges = document.createElement('div');
    badges.className = 'flex flex-wrap gap-2 mb-2';
    sec.pageAnchors.slice(0, 8).forEach(p => {
      const b = document.createElement('span');
      b.className = 'inline-flex items-center rounded-full bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 text-xs';
      b.textContent = `p${p}`;
      badges.appendChild(b);
    });
    wrap.appendChild(badges);
  }
  const ul = document.createElement('ul');
  ul.className = 'list-disc pl-6 space-y-1 text-sm text-gray-800';
  (sec.bullets || []).forEach(b => {
    const li = document.createElement('li');
    li.textContent = b;
    ul.appendChild(li);
  });
  if ((sec.bullets || []).length === 0) {
    const p = document.createElement('p');
    p.className = 'text-sm text-gray-600';
    p.textContent = '(no items)';
    wrap.appendChild(p);
  } else {
    wrap.appendChild(ul);
  }
  if (sec.citations && sec.citations.length) {
    const row = document.createElement('div');
    row.className = 'mt-3 flex items-center justify-between';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'text-xs text-blue-700 hover:underline';
    btn.textContent = 'Show citations';
    const pre = document.createElement('pre');
    pre.className = 'mt-2 bg-gray-50 rounded-md p-3 text-xs citations';
    pre.textContent = sec.citations.map(c => `p${c.page_start}-${c.page_end}  ${c.filename || ''}`).join('\n');
    btn.addEventListener('click', () => {
      const hidden = pre.style.display === '' || pre.style.display === 'none';
      pre.style.display = hidden ? 'block' : 'none';
      btn.textContent = hidden ? 'Hide citations' : 'Show citations';
    });
    row.appendChild(btn);
    wrap.appendChild(row);
    wrap.appendChild(pre);
  }
  return wrap;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const subject = document.getElementById('teachSubject').value || '';
  const chapter = document.getElementById('teachChapter').value || '';
  const topicsRaw = document.getElementById('teachTopics').value || '';
  const retriever = document.getElementById('teachRetriever').value || 'auto';
  const depth = document.getElementById('teachDepth')?.value || 'standard';
  const k = document.getElementById('teachK').value || '10';
  const topics = topicsRaw.split(/\n|,/).map(s => s.trim()).filter(Boolean);

  const btn = form.querySelector('button[type="submit"]');
  setBusy(btn, true, 'Generating...');
  resultEl.innerHTML = '';
  try {
    const ac = new AbortController();
    const res = await postTeach({ subject, chapter, topics, retriever, k: Number(k), depth }, ac.signal);
    if (!res.ok) throw new Error(await res.text());
    const json = await res.json();
    const outline = json.outline || [];
    outline.forEach(sec => resultEl.appendChild(renderSection(sec)));
    if (json.readingList && json.readingList.length) {
      const rl = document.createElement('div');
      rl.className = 'text-xs text-gray-600';
      rl.textContent = 'Reading list: ' + json.readingList.map(r => `p${r.page}`).join(', ');
      resultEl.appendChild(rl);
    }
    // Glossary highlight
    const glossary = json.glossary || [];
    const terms = glossary.map(g => g.term).filter(Boolean);
    if (terms.length) {
      resultEl.querySelectorAll('li').forEach(li => {
        let t = li.textContent;
        terms.forEach(term => {
          const re = new RegExp(`\\b${term.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')}\\b`, 'g');
          t = t.replace(re, '<mark class="bg-yellow-200">' + term + '</mark>');
        });
        li.innerHTML = t;
      });
    }
  } catch (err) {
    showToast(`Teach failed: ${err}`, 'error');
  } finally {
    setBusy(btn, false);
  }
});

// Copy and Print actions
copyBtn?.addEventListener('click', async () => {
  try {
    const txt = Array.from(document.querySelectorAll('#teachResult section'))
      .map(sec => {
        const title = sec.querySelector('h3')?.textContent || '';
        const bullets = Array.from(sec.querySelectorAll('li')).map(li => '• ' + li.textContent).join('\n');
        return title + '\n' + bullets;
      }).join('\n\n');
    await navigator.clipboard.writeText(txt);
    showToast('Outline copied');
  } catch (e) {
    showToast('Copy failed', 'error');
  }
});

printBtn?.addEventListener('click', () => window.print());
