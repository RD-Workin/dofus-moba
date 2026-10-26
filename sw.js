// Hors ligne : la page et le moteur sont gardés sur le téléphone après le premier chargement complet.
// package_mobile.py remplace 96caa2bf0a (empreinte du contenu) : une nouvelle version vide l'ancien cache.
const CACHE = 'kolizeum-96caa2bf0a';
const ASSETS = ["./", "manifest.webmanifest", "g0.46fcf831.wasm", "g1.67dba631.wasm", "g2.4de7489e.wasm", "g3.8e7887e5.wasm", "game.audio.position.worklet.js", "game.audio.worklet.js", "game.js", "p0.ed289547.wasm", "p1.1c5c7573.wasm", "p2.a509fcfd.wasm", "p3.6e15a2ff.wasm", "icons/icon-180.png", "icons/icon-192.png", "icons/icon-512.png"];

const HASHED = f => /^[gp]\d+\.[0-9a-f]{8}\.wasm$/.test(f);

// Les morceaux du jeu portent l'empreinte de leur contenu : on les reprend du cache du navigateur (la page vient de
// les télécharger) ; les autres fichiers sont revérifiés auprès du serveur pour ne jamais garder une ancienne copie.
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE)
    .then(c => c.addAll(ASSETS.map(f => new Request(f, { cache: HASHED(f) ? 'force-cache' : 'no-cache' }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith('kolizeum-') && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin || url.pathname.endsWith('/version.json')) return;
  // La page passe d'abord par le réseau : chaque lancement en ligne prend la dernière version publiée.
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req, { cache: 'no-cache' })
      .catch(() => caches.open(CACHE).then(c => c.match('./')))
      .then(res => res || Response.error()));
    return;
  }
  const key = req;
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(key, { ignoreSearch: true });
    if (hit) return hit;
    const res = await fetch(req);
    if (res.ok && res.type === 'basic') c.put(key, res.clone());
    return res;
  }));
});
