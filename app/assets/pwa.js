if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register(location.pathname.includes('/textos/') ? '../sw.js' : './sw.js');
}
