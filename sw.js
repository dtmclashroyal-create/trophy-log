// 앱 화면과 기록은 항상 최신을 먼저 받고(인터넷이 없으면 저장해 둔 것),
// 아이콘·폰트·카드 이미지처럼 잘 안 바뀌는 것은 저장해 둔 것을 먼저 써요.
const CACHE = 'trophy-log-v5';
const SHELL = ['./', 'index.html', 'manifest.webmanifest', 'icon.svg', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

function networkFirst(req, key) {
  return fetch(req).then(r => {
    if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(key || req, copy)); }
    return r;
  }).catch(() => caches.match(key || req));
}

function cacheFirst(req) {
  return caches.match(req).then(hit => hit || fetch(req).then(r => {
    if (r.ok || r.type === 'opaque') { const copy = r.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return r;
  }));
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const same = url.origin === location.origin;
  if (same && url.pathname.endsWith('/data/battles.json')) return e.respondWith(networkFirst(req, 'data/battles.json'));
  if (req.mode === 'navigate' || (same && /\.(html|js|webmanifest)$/.test(url.pathname))) return e.respondWith(networkFirst(req));
  e.respondWith(cacheFirst(req));
});
