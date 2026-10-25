// Hors ligne : la page et le moteur sont gardés sur le téléphone après le premier chargement complet.
// package_mobile.py remplace __VERSION__ (empreinte du contenu) : une nouvelle version vide l'ancien cache.
const CACHE = 'kolizeum-__VERSION__';
const ASSETS = __ASSETS__;

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
