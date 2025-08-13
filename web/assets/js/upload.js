import { API_BASE } from './config.js?v=5';
import { showToast, setBusy } from './ui.js';

const form = document.getElementById('uploadForm');
const out = document.getElementById('uploadResult');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(form);
  out.textContent = 'Uploading...';
  const btn = form.querySelector('button[type="submit"]');
  setBusy(btn, true, 'Uploading...');
  try {
    const ac = new AbortController();
  const t = setTimeout(() => ac.abort('timeout'), 180000);
    let res;
    const url1 = `${API_BASE}/data/upload`;
    try {
      res = await fetch(url1, { method: 'POST', body: fd, signal: ac.signal });
    } catch (e) {
      // Fallback to same-origin
      res = await fetch('/data/upload', { method: 'POST', body: fd, signal: ac.signal });
    }
    clearTimeout(t);
    if (!res.ok) {
      const msg = await res.text().catch(() => `${res.status}`);
      throw new Error(msg || `HTTP ${res.status}`);
    }
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
    showToast('Upload complete', 'success');
  } catch (err) {
  const msg = String(err && err.message ? err.message : err);
  let hint = '';
  if (msg === 'timeout' || /AbortError/i.test(msg)) hint = ' (request timed out)';
  if (/Failed to fetch/i.test(msg)) hint = ' (server not reachable — is API running?)';
  out.textContent = `Error: ${msg}${hint}`;
  showToast(`Upload failed: ${msg}${hint}`, 'error');
  } finally {
    setBusy(btn, false);
  }
});
