// Minimal PWA helpers: install button and online/offline indicator
const installBtn = document.getElementById('installBtn');
const installMsg = document.getElementById('installMsg');
const netStatus = document.getElementById('netStatus');

// Network status dot
function updateNetStatus() {
  const online = navigator.onLine;
  netStatus.textContent = online ? '● online' : '● offline';
  netStatus.className = `net-dot ${online ? 'net-online' : 'net-offline'}`;
}
window.addEventListener('online', updateNetStatus);
window.addEventListener('offline', updateNetStatus);
updateNetStatus();

// Install prompt
let deferredPrompt = null;

// Hide button if we're already in standalone (installed)
const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
if (isStandalone) {
  installBtn.classList.add('hidden');
  installMsg.textContent = 'App is installed';
}
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  installBtn.classList.remove('hidden');
  installMsg.textContent = 'Ready to install';
});

installBtn?.addEventListener('click', async () => {
  if (!deferredPrompt) {
    // Fallback guidance for Edge/Chrome when prompt is throttled/not fired yet
    installMsg.textContent = 'If no prompt appears, use Edge menu: … > Apps > Install this site as an app (or the install icon in the address bar).';
    return;
  }
  try {
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    installMsg.textContent = outcome === 'accepted' ? 'Installed' : 'Installation dismissed';
  } finally {
    installBtn.classList.add('hidden');
    deferredPrompt = null;
  }
});

window.addEventListener('appinstalled', () => {
  installBtn.classList.add('hidden');
  installMsg.textContent = 'App installed';
});

// If the button is visible but click does nothing, surface a hint
function showNotEligibleHint() {
  installMsg.textContent = 'Install will appear after the page is fully loaded and controlled by the service worker. In Edge/Chrome, try a reload if you dismissed earlier.';
}

// On load, if no deferredPrompt after a short delay, show a hint
window.addEventListener('load', () => {
  setTimeout(() => {
    if (!deferredPrompt && !isStandalone) {
      showNotEligibleHint();
    }
  }, 1500);
});
