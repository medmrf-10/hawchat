const CACHE='hawchat-v4';
const ASSETS=['./','./index.html','./theme.css','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{e.respondWith(
  fetch(e.request).then(r=>{
    if(e.request.method==='GET'&&r.ok){const c=r.clone();caches.open(CACHE).then(cc=>cc.put(e.request,c))}
    return r;
  }).catch(()=>caches.match(e.request))
)});
