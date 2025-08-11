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
  ans.textContent = 'Thinking...';
  citesEl.textContent = '';
  passagesEl.textContent = '';
  try {
    const url = new URL(`${API_BASE}/ask`);
    url.searchParams.set('q', q);
    if (subject) url.searchParams.set('subject', subject);
    if (chapter) url.searchParams.set('chapter', chapter);
    url.searchParams.set('k', '6');
    url.searchParams.set('answer_synthesis', 'true');
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
  } catch (err) {
    ans.textContent = `Error: ${err}`;
  }
});
