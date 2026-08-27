document.addEventListener('DOMContentLoaded', () => {
  const sheet = document.querySelector('#authSheet');
  const status = document.querySelector('#authStatus');
  const account = document.querySelector('#accountButton');
  const config = window.TRAZO_SUPABASE || {};
  let previewing = sessionStorage.getItem('trazo-preview') === '1';
  if (config.requireAuth) previewing = false;
  document.querySelector('#previewAccess').hidden = Boolean(config.requireAuth);
  const render = event => {
    const state = event?.detail || window.trazoData?.state || {};
    const required = Boolean(config.requireAuth);
    sheet.classList.toggle('visible', !state.user && !previewing && (required || !sessionStorage.getItem('trazo-auth-seen')));
    account.textContent = state.user ? (state.user.email?.split('@')[0] || 'Cuenta') : 'Acceder';
  };
  window.addEventListener('trazo:auth', render);
  document.querySelector('#googleLogin').addEventListener('click', async () => { try { status.textContent = 'Abriendo Google…'; await window.trazoData.google(); } catch (error) { status.textContent = error.message; } });
  document.querySelector('#magicLinkForm').addEventListener('submit', async event => { event.preventDefault(); try { status.textContent = 'Enviando enlace…'; await window.trazoData.magicLink(document.querySelector('#authEmail').value); status.textContent = 'Revisa tu correo para entrar.'; } catch (error) { status.textContent = error.message; } });
  document.querySelector('#previewAccess').addEventListener('click', () => { if (config.requireAuth) return; previewing = true; sessionStorage.setItem('trazo-preview', '1'); sessionStorage.setItem('trazo-auth-seen', '1'); render(); });
  account.addEventListener('click', async () => { if (window.trazoData.state.user) { await window.trazoData.signOut(); previewing = false; } else { previewing = false; sheet.classList.add('visible'); } });
  render();
  if ('serviceWorker' in navigator) navigator.serviceWorker.register(location.pathname.includes('/textos/') ? '../sw.js' : './sw.js');
});
