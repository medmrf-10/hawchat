/* hawchat service worker v7 — 3-tier cache.
   shell: app assets (html/css/js/fonts/icons) — versioned, replaced per deploy.
   data:  JSON (stats, read rows, series) — stale-while-revalidate.
   text:  transcripts/alignments/images — cache-first, LRU-bounded, version-stable.
   No auto skipWaiting: pages show an update toast; users opt in. */
const REV = 'v8-39x';
const SHELL = 'hawchat-shell-' + REV;
const DATA  = 'hawchat-data-' + REV;   // versioned with the build — no stale mixes
const TEXT  = 'hawchat-text-v1';
const PIN   = 'hawchat-pinned-v1';   // user-saved rows — never LRU-trimmed
const KEEP  = [SHELL, DATA, TEXT, PIN];
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
  // resilient: a single missing asset must not kill the whole install
  e.waitUntil(caches.open(SHELL).then(async c => {
    await Promise.all(SHELL_ASSETS.map(u => c.add(u).catch(() => null)));
  }));
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

// true LRU: a hit re-queues the entry so hot rows are never evicted
async function touch(c, req, hit) {
  try { await c.put(req, hit.clone()); } catch (e) {}
}

async function netFirst(req, cacheName, timeoutMs) {
  try {
    const r = await Promise.race([
      fetch(req),
      new Promise((_, rj) => setTimeout(() => rj(new Error('timeout')), timeoutMs)),
    ]);
    if (r.ok) { const c = await caches.open(cacheName); c.put(req, r.clone()); }
    return r;
  } catch (err) {
    const hit = await caches.match(req);
    if (hit) return hit;
    if (req.mode === 'navigate' || req.destination === 'document') {
      const off = await caches.match('./offline.html');
      if (off) return off;
    }
    throw err;
  }
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (u.origin !== location.origin) return;
  const p = u.pathname;

  // HTML documents: network-first (3s) → cache → offline page
  if (req.destination === 'document' || /\.(html|\/)$/.test(p) || !p.includes('.')) {
    e.respondWith(netFirst(req, SHELL, 3000));
    return;
  }

  // shell assets (css/js/fonts/icons): cache-first, refreshed per REV
  if (/\.(css|js|woff2?)$/.test(p) || p.includes('/icons/') || p.endsWith('/manifest.webmanifest')) {
    e.respondWith(caches.open(SHELL).then(async c => {
      const hit = await c.match(req, {ignoreSearch: true});
      if (hit) return hit;
      const r = await fetch(req);
      if (r.ok) c.put(req, r.clone());
      return r;
    }));
    return;
  }

  // JSON data: stale-while-revalidate (stats get fresh copy in background)
  if (/\.json$/.test(p)) {
    e.respondWith(caches.open(DATA).then(async c => {
      const hit = await c.match(req);
      const up = fetch(req).then(r => {
        if (r.ok) { c.put(req, r.clone()); trim(c); }
        return r;
      }).catch(() => hit);
      return hit || up;
    }));
    return;
  }

  // transcripts / alignments / images: stale-while-revalidate + LRU.
  // SWR matters: a corrected transcription reaches prior visitors on next read.
  if (/\.(txt|jpg|jpeg|png|webp|svg|mp4)$/.test(p) || p.includes('.align.')) {
    e.respondWith((async () => {
      const ph = await (await caches.open(PIN)).match(req);
      if (ph) return ph;                        // user-saved copy always wins
      const c = await caches.open(TEXT);
      const hit = await c.match(req);
      const up = fetch(req).then(r => {
        if (r.ok) { c.put(req, r.clone()); trim(c); }
        return r;
      }).catch(() => hit);
      if (hit) { touch(c, req, hit); return hit; }
      return up;
    })());
  }
});
