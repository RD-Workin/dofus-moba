// Hors ligne : la page et le moteur sont gardés sur le téléphone après le premier chargement complet.
// package_mobile.py remplace fa6638c583 (empreinte du contenu) : une nouvelle version vide l'ancien cache.
const CACHE = 'kolizeum-fa6638c583';
const ASSETS = ["./", "manifest.webmanifest", "g0.wasm", "g1.wasm", "g2.wasm", "g3.wasm", "game.audio.position.worklet.js", "game.audio.worklet.js", "game.js", "p0.wasm", "p1.wasm", "p2.wasm", "icons/icon-180.png", "icons/icon-192.png", "icons/icon-512.png"];

// Au premier lancement la page télécharge le jeu avant que ce script ne soit actif : on reprend les mêmes fichiers
// depuis le cache du navigateur (« force-cache ») pour ne pas tout retélécharger.
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE)
    .then(c => c.addAll(ASSETS.map(f => new Request(f, { cache: 'force-cache' }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith('kolizeum-') && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  const key = req.mode === 'navigate' ? './' : req;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(key, { ignoreSearch: true });
    if (hit) return hit;
    const res = await fetch(req);
    if (res.ok && res.type === 'basic') c.put(key, res.clone());
    return res;
  }));
});
