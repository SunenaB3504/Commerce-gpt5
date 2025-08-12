import { API_BASE } from './config.js';

const form = document.getElementById('askForm');
const ans = document.getElementById('askAnswer');
const citesEl = document.getElementById('askCitations');
const passagesEl = document.getElementById('askPassages');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const subject = document.getElementById('askSubject').value || '';
  const chapter = document.getElementById('askChapter').value || '';
  const q = document.getElementById('askQ').value || '';
  const k = document.getElementById('askK')?.value || '10';
  const filter = document.getElementById('askFilter')?.checked;
  const stream = document.getElementById('askStream')?.checked;
  ans.textContent = 'Thinking...';
  citesEl.textContent = '';
  passagesEl.textContent = '';
  try {
    const base = stream ? `${API_BASE}/ask/stream` : `${API_BASE}/ask`;
    const url = new URL(base);
    url.searchParams.set('q', q);
    if (subject) url.searchParams.set('subject', subject);
    if (chapter) url.searchParams.set('chapter', chapter);
  url.searchParams.set('k', String(k));
    url.searchParams.set('answer_synthesis', 'true');
    if (filter) url.searchParams.set('filter_noise', 'true');

    if (stream) {
      const es = new EventSource(url);
      es.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data || '{}');
          if (data.type === 'passage') {
            const r = data;
            const meta = r.metadata || {};
            const p = `p${meta.page_start}-${meta.page_end}`;
            const t = (r.text || '').slice(0, 160);
            passagesEl.textContent += `${p}  ${t}\n`;
          } else if (data.type === 'answer') {
            ans.textContent = data.text || '(no answer)';
            if (data.citations && data.citations.length) {
              const lines = data.citations.map(c => `p${c.page_start}-${c.page_end}  ${c.filename || ''}`);
              citesEl.textContent = lines.join('\n');
            }
            es.close();
          }
        } catch {}
      };
      es.onerror = () => {
        es.close();
      };
    } else {
      const res = await fetch(url);
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      ans.textContent = json.answer || '(no answer)';
      if (json.citations && json.citations.length) {
        const lines = json.citations.map(c => `p${c.page_start}-${c.page_end}  ${c.filename || ''}`);
        citesEl.textContent = lines.join('\n');
      }
      if (json.results && json.results.length) {
        const top = json.results.slice(0, 5).map(r => {
          const p = `p${r.metadata.page_start}-${r.metadata.page_end}`;
          const t = r.text.length > 160 ? r.text.slice(0,160) + '.' : r.text;
          return `${p}  dist=${(r.distance ?? 0).toFixed(3)}  ${t}`;
        });
        passagesEl.textContent = top.join('\n');
      }
    }
  } catch (err) {
    ans.textContent = `Error: ${err}`;
  }
});
