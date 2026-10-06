/* hawshat service worker v7 — 3-tier cache.
   shell: app assets (html/css/js/fonts/icons) — versioned, replaced per deploy.
   data:  JSON (stats, read rows, series) — stale-while-revalidate.
   text:  transcripts/alignments/images — cache-first, LRU-bounded, version-stable.
   No auto skipWaiting: pages show an update toast; users opt in.

   REV discipline (see playlists/README.md):
   - *.html                     → network-first 3s; bumped content ships free.
   - css/js/fonts/icons/manifest → cache-first per REV + ?v= (search-significant);
                                 bump ?v= when the asset changes inside a REV.
   - *.json                     → SWR in DATA (wiped per REV).
   - *.txt/.align.*/icons.svg/images → SWR in TEXT (REV-stable). */
const REV = 'v8-52';
const SHELL = 'hawshat-shell-' + REV;
const DATA  = 'hawshat-data-' + REV;   // versioned with the build — no stale mixes
const TEXT  = 'hawshat-text-v1';
const PIN   = 'hawshat-pinned-v1';   // user-saved rows — never LRU-trimmed
const KEEP  = [SHELL, DATA, TEXT, PIN];
const MAXE  = 250;                              // LRU bound for text/data caches

const SHELL_ASSETS = [
  './', './index.html', './theme.css', './manifest.webmanifest', './offline.html',
  './fonts/fonts.css',
  './playlists/', './playlists/index.html', './playlists/sheikh.html',
  './playlists/series.html', './playlists/tr.html', './playlists/lesson.html',
  './playlists/common.css', './playlists/common.js',
  './playlists/ui.css', './playlists/icons.svg', './playlists/row.html',
  './playlists/yt.html', './playlists/sm.html', './playlists/qu.html', './playlists/aud.html',
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

const NO_NET = () => new Response('', {status: 504, statusText: 'offline'});

async function netFirst(req, cacheName, timeoutMs) {
  const u = new URL(req.url);
  // documents are keyed by path only — one template serves every query variant
  const key = new Request(u.origin + u.pathname);
  try {
    const r = await Promise.race([
      fetch(req),
      new Promise((_, rj) => setTimeout(() => rj(new Error('timeout')), timeoutMs)),
    ]);
    if (r.ok) { const c = await caches.open(cacheName); c.put(key, r.clone()); }
    return r;
  } catch (err) {
    // last visit's template, regardless of ?s=&l= this navigation carries
    const hit = await caches.match(key, {ignoreSearch: true});
    if (hit) return hit;
    if (req.mode === 'navigate' || req.destination === 'document') {
      const off = await caches.match('./offline.html');
      if (off) return off;
    }
    return NO_NET();
  }
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (u.origin !== location.origin) return;
  const p = u.pathname;

  // HTML documents: network-first (3s) → cached template (ignoreSearch) → offline page
  if (req.destination === 'document' || /\.(html|\/)$/.test(p) || !p.includes('.')) {
    e.respondWith(netFirst(req, SHELL, 3000));
    return;
  }

  // shell assets (css/js/fonts/icons/manifest): cache-first, refreshed per REV.
  // ?v= is significant — a page asking ?v=9 must not be served a ?v=8 body.
  if (/\.(css|js|woff2?)$/.test(p) || p.includes('/icons/') || p.endsWith('/icons.svg')
      || p.endsWith('/manifest.webmanifest')) {
    e.respondWith(caches.open(SHELL).then(async c => {
      const hit = await c.match(req);
      if (hit) return hit;
      const r = await fetch(req).catch(() => null);
      if (r && r.ok) { c.put(req, r.clone()); return r; }
      return NO_NET();
    }));
    return;
  }

  // word alignments: heavy, long-lived — TEXT tier (survives REV bumps).
  if (p.includes('.align.')) {
    e.respondWith((async () => {
      const ph = await (await caches.open(PIN)).match(req);
      if (ph) return ph;
      const c = await caches.open(TEXT);
      const hit = await c.match(req);
      const up = fetch(req).then(r => {
        if (r.ok) { c.put(req, r.clone()); trim(c); }
        return r;
      }).catch(() => hit || NO_NET());
      if (hit) { touch(c, req, hit); return hit; }
      return up;
    })());
    return;
  }

  // JSON data: pinned copies first (user-saved), then stale-while-revalidate.
  if (/\.json$/.test(p)) {
    e.respondWith((async () => {
      const ph = await (await caches.open(PIN)).match(req);
      if (ph) return ph;
      const c = await caches.open(DATA);
      const hit = await c.match(req);
      const up = fetch(req).then(r => {
        if (r.ok) { c.put(req, r.clone()); trim(c); }
        return r;
      }).catch(() => hit || NO_NET());
      return hit || up;
    })());
    return;
  }

  // transcripts / images: stale-while-revalidate + LRU.
  // SWR matters: a corrected transcription reaches prior visitors on next read.
  if (/\.(txt|jpg|jpeg|png|webp|svg|mp4)$/.test(p)) {
    e.respondWith((async () => {
      const ph = await (await caches.open(PIN)).match(req);
      if (ph) return ph;                        // user-saved copy always wins
      const c = await caches.open(TEXT);
      const hit = await c.match(req);
      const up = fetch(req).then(r => {
        if (r.ok) { c.put(req, r.clone()); trim(c); }
        return r;
      }).catch(() => hit || NO_NET());
      if (hit) { touch(c, req, hit); return hit; }
      return up;
    })());
  }
});
