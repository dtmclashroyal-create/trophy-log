// 앱 화면은 캐시해서 오프라인에서도 열리고, 기록 데이터는 항상 최신을 먼저 시도해요.
const CACHE = 'trophy-log-v1';
const SHELL = ['./', 'index.html', 'manifest.webmanifest', 'icon.svg', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (url.origin === location.origin && url.pathname.endsWith('/data/battles.json')) {
    // 네트워크 우선, 실패하면 마지막으로 받은 기록
    e.respondWith(fetch(e.request).then(r => {
      const copy = r.clone();
      caches.open(CACHE).then(c => c.put('data/battles.json', copy));
      return r;
    }).catch(() => caches.match('data/battles.json')));
    return;
  }
  // 그 외(화면, 아이콘, 폰트): 캐시 우선, 없으면 받아서 저장
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {
    if (r.ok || r.type === 'opaque') { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
    return r;
  })));
});
