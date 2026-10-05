const CACHE='hawchat-v6';
const MAXE=200;
const ASSETS=['./','./index.html','./theme.css','./playlists/common.css','./playlists/common.js','./manifest.webmanifest','./icons/icon-192.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
function key(req){const u=new URL(req.url);u.search='';return new Request(u.href,{method:'GET'})}
async function trim(c){const ks=await c.keys();if(ks.length>MAXE)await c.delete(ks[0])}
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(e.request.method!=='GET'||u.origin!==location.origin)return;   // same-origin only
  const p=u.pathname;
  if(/\.(html|\/)$/.test(p)||!p.includes('.')){                       // HTML: network-first, 3s timeout
    e.respondWith(Promise.race([fetch(e.request).then(r=>{if(r.ok)caches.open(CACHE).then(c=>c.put(key(e.request),r.clone()));return r}),
      new Promise((_,rj)=>setTimeout(()=>rj(new Error('t/o')),3000))]).catch(()=>caches.match(key(e.request))));
    return;
  }
  if(p.endsWith('/sheikh_stats.json')){                              // stats: network-first, falls back to cache
    e.respondWith(fetch(e.request).then(r=>{if(r.ok)caches.open(CACHE).then(c=>c.put(key(e.request),r.clone()));return r})
      .catch(()=>caches.match(key(e.request))));
    return;
  }
  if(/\.json$/.test(p)){                                             // JSON: stale-while-revalidate
    e.respondWith(caches.open(CACHE).then(async c=>{
      const k=key(e.request),hit=await c.match(k);
      const up=fetch(e.request).then(r=>{if(r.ok){c.put(k,r.clone());trim(c)}return r}).catch(()=>hit);
      return hit||up;
    }));
    return;
  }
  if(/\.(txt|jpg|png|webp|css|js)$/.test(p)||p.includes('.align.')){   // static: cache-first, bounded
    e.respondWith(caches.open(CACHE).then(async c=>{
      const k=key(e.request),hit=await c.match(k);
      if(hit)return hit;
      const r=await fetch(e.request);if(r.ok){c.put(k,r.clone());trim(c)}return r;
    }));
  }
});
