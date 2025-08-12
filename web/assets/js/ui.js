export function showToast(message, type = 'info', timeout = 3500) {
  let box = document.getElementById('toastBox');
  if (!box) {
    box = document.createElement('div');
    box.id = 'toastBox';
    document.body.appendChild(box);
  }
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = message;
  box.appendChild(el);
  setTimeout(() => {
    el.classList.add('toast-out');
    setTimeout(() => el.remove(), 250);
  }, timeout);
}

export function setBusy(buttonEl, busy = true, busyText = 'Working...') {
  if (!buttonEl) return;
  if (busy) {
    buttonEl.dataset.prevText = buttonEl.textContent;
    buttonEl.textContent = busyText;
    buttonEl.disabled = true;
  } else {
    if (buttonEl.dataset.prevText) buttonEl.textContent = buttonEl.dataset.prevText;
    buttonEl.disabled = false;
  }
}
