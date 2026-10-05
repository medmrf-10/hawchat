<<<<<<< HEAD
const CACHE='hawchat-v5';
const ASSETS=['./','./index.html','./theme.css','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{e.respondWith(
  fetch(e.request).then(r=>{
    if(e.request.method==='GET'&&r.ok){const c=r.clone();caches.open(CACHE).then(cc=>cc.put(e.request,c))}
||||||| parent of 2fb6563 (rebuild generated data)
/* hawchat service worker v7 — 3-tier cache.
   shell: app assets (html/css/js/fonts/icons) — versioned, replaced per deploy.
   data:  JSON (stats, read rows, series) — stale-while-revalidate.
   text:  transcripts/alignments/images — cache-first, LRU-bounded, version-stable.
   No auto skipWaiting: pages show an update toast; users opt in. */
const REV = 'v7-'f6b091b'ec8e92d'228d96c'344430e'14a0ae6'd8f34b5'8b5085c'8ea2c5c';                               // stamped by safe_push
const SHELL = 'hawchat-shell-' + REV;
const DATA  = 'hawchat-data-v1';
const TEXT  = 'hawchat-text-v1';
const KEEP  = [SHELL, DATA, TEXT];
const MAXE  = 250;                              // LRU bound for text/data caches

const SHELL_ASSETS = [
  './', './index.html', './theme.css', './manifest.webmanifest', './offline.html',
  './fonts/fonts.css',
  './playlists/', './playlists/index.html', './playlists/sheikh.html',
  './playlists/series.html', './playlists/tr.html', './playlists/lesson.html',
  './playlists/common.css', './playlists/common.js',
  './playlists/ui.css', './playlists/icons.svg', './playlists/row.html',
  './icons/icon-192.png',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_ASSETS)));
  // NO skipWaiting — the update toast asks the user first.
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => !KEEP.includes(k)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', e => {
  if (e.data === 'SKIP_WAITING') self.skipWaiting();
});

async function trim(c) {
  const ks = await c.keys();
  if (ks.length > MAXE) await c.delete(ks[0]);
}

async function netFirst(req, cacheName, timeoutMs) {
  try {
    const r = await Promise.race([
      fetch(req),
      new Promise((_, rj) => setTimeout(() => rj(new Error('timeout')), timeoutMs)),
    ]);
    if (r.ok) { const c = await caches.open(cacheName); c.put(req, r.clone()); }
=======
/* hawchat service worker v7 — 3-tier cache.
   shell: app assets (html/css/js/fonts/icons) — versioned, replaced per deploy.
   data:  JSON (stats, read rows, series) — stale-while-revalidate.
   text:  transcripts/alignments/images — cache-first, LRU-bounded, version-stable.
   No auto skipWaiting: pages show an update toast; users opt in. */
const REV = 'v7-'f7873e9'8a399d3'ed400ac'660e8fb'1fae3c2'ce4803a'c4d671f'af93226'2fb6563'4cd5eeb'f6b091b'ec8e92d'228d96c'344430e'14a0ae6'd8f34b5'8b5085c'8ea2c5c';                               // stamped by safe_push
const SHELL = 'hawchat-shell-' + REV;
const DATA  = 'hawchat-data-v1';
const TEXT  = 'hawchat-text-v1';
const KEEP  = [SHELL, DATA, TEXT];
const MAXE  = 250;                              // LRU bound for text/data caches

const SHELL_ASSETS = [
  './', './index.html', './theme.css', './manifest.webmanifest', './offline.html',
  './fonts/fonts.css',
  './playlists/', './playlists/index.html', './playlists/sheikh.html',
  './playlists/series.html', './playlists/tr.html', './playlists/lesson.html',
  './playlists/common.css', './playlists/common.js',
  './playlists/ui.css', './playlists/icons.svg', './playlists/row.html',
  './icons/icon-192.png',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_ASSETS)));
  // NO skipWaiting — the update toast asks the user first.
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => !KEEP.includes(k)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', e => {
  if (e.data === 'SKIP_WAITING') self.skipWaiting();
});

async function trim(c) {
  const ks = await c.keys();
  if (ks.length > MAXE) await c.delete(ks[0]);
}

async function netFirst(req, cacheName, timeoutMs) {
  try {
    const r = await Promise.race([
      fetch(req),
      new Promise((_, rj) => setTimeout(() => rj(new Error('timeout')), timeoutMs)),
    ]);
    if (r.ok) { const c = await caches.open(cacheName); c.put(req, r.clone()); }
>>>>>>> 2fb6563 (rebuild generated data)
    return r;
  }).catch(()=>caches.match(e.request))
)});
