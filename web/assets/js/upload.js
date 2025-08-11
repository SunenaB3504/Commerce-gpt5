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
    out.textContent = JSON.stringify(json, null, 2);
  } catch (err) {
    out.textContent = `Error: ${err}`;
  }
});
