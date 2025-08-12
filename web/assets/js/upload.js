import { API_BASE } from './config.js';

const form = document.getElementById('uploadForm');
const out = document.getElementById('uploadResult');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(form);
  out.textContent = 'Uploading...';
  try {
    const res = await fetch(`${API_BASE}/data/upload`, { method: 'POST', body: fd });
    if (!res.ok) throw new Error(await res.text());
    const json = await res.json();
    const lines = [
      `id: ${json.id}`,
      `filename: ${json.filename}`,
      `path: ${json.path}`,
      `subject: ${json.subject || ''}`,
      `chapter: ${json.chapter || ''}`,
    ];
    if (json.auto_index) {
      lines.push(`namespace: ${json.namespace || ''}`);
      lines.push(`index_count: ${json.index_count ?? ''}`);
      if (json.chunks_path) lines.push(`chunks_path: ${json.chunks_path}`);
    }
    out.textContent = lines.join('\n');
  } catch (err) {
    out.textContent = `Error: ${err}`;
  }
});
