/* common.js — shared helpers for سلاسل المشايخ */
function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function j(u){try{const r=await fetch(u,{cache:'no-cache'});return r.ok?await r.json():null}catch(e){return null}}
async function jtxt(u){try{const c=new AbortController();const t=setTimeout(()=>c.abort(),20000);const r=await fetch(u,{signal:c.signal});clearTimeout(t);return r.ok?await r.text():null}catch(e){return null}}
function normalize(s){return (s||'').replace(/[أإآ]/g,'ا').replace(/[ً-ْٰ]/g,'').replace(/ـ/g,'').replace(/ى/g,'ي').replace(/ة/g,'ه').replace(/\s+/g,' ').trim()}
const _PR=new Intl.PluralRules('ar');
function plural(n,one,two,few,many){const c=_PR.select(n);return c==='one'?one:c==='two'?two:c==='few'?few:many}
function pluralSeries(n){return n===1?'سلسلة واحدة':n===2?'سلسلتان':plural(n,'سلسلة','سلسلتان',n+' سلاسل',n+' سلسلةً')}
function pluralLesson(n){return n===1?'درس واحد':n===2?'درسان':plural(n,'درس','درسان',n+' دروس',n+' درساً')}
/* inline SVG icons: read=open book, listen=headphones, check, chev */
const I={
 read:'<svg class="i ic-read" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3.2C6.6 2 4.6 1.5 2 1.5v11c2.6 0 4.6.5 6 1.7 1.4-1.2 3.4-1.7 6-1.7v-11c-2.6 0-4.6.5-6 1.7zm0 10.1V3.2" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>',
 listen:'<svg class="i ic-listen" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 10V8a5 5 0 0 1 10 0v2"/><rect x="2" y="9" width="3.4" height="5" rx="1.4" fill="currentColor" stroke="none"/><rect x="10.6" y="9" width="3.4" height="5" rx="1.4" fill="currentColor" stroke="none"/></svg>',
 check:'<svg class="i ic-check" viewBox="0 0 16 16" aria-hidden="true"><path d="M13.8 3.2 6.2 10.8 2.6 7.2l-1.4 1.4 5 5 9-9z"/></svg>',
 chev:'<svg class="i" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M10 3 5 8l5 5"/></svg>'
};
/* unified stat chip: icon + N(✓ if complete) or n/t + thin progress bar */
function statChip(kind,n,tot,ok){
 const ic=kind==='read'?I.read:I.listen;
 const done=n>0&&tot>0&&n>=tot;
 const shown=done?('<b>'+n+'</b><span class="ok">'+I.check+'</span>'):('<b>'+(tot&&tot>n?n+'/'+tot:n)+'</b>');
 const pct=tot>0?Math.min(100,Math.round(100*n/tot)):(n>0?100:0);
 const lbl=(kind==='read'?'يُقرأ':'يُسمع')+': '+(done?n+' درساً، مكتمل':n+' من '+tot+' درساً');
 return '<span class="stat'+(kind==='listen'?' lst':'')+'" role="img" aria-label="'+lbl+'"><span class="row">'+ic+shown+'</span><span class="bar"><i style="width:'+pct+'%"></i></span></span>';
}
/* standard header + optional breadcrumb links [{h,t}] */
function hdr(sub,crumb){
 let c='';
 if(crumb&&crumb.length)c='<nav class="crumb" aria-label="مسار التنقل">'+crumb.map((x,i)=>(i?' ‹ ':'')+(x.h?'<a href="'+x.h+'">'+esc(x.t)+'</a>':esc(x.t))).join('')+'</nav>';
 return c;
}
/* service worker: register + update toast (no auto-reload) */
function swRegister(path){
 if(!('serviceWorker' in navigator))return;
 navigator.serviceWorker.register(path).then(reg=>{
  reg.addEventListener('updatefound',()=>{
   const w=reg.installing;if(!w)return;
   w.addEventListener('statechange',()=>{
    if(w.state==='installed'&&navigator.serviceWorker.controller)showUpdToast(reg);
   });
  });
 }).catch(()=>{});
}
function showUpdToast(reg){
 if(document.getElementById('updtoast'))return;
 const t=document.createElement('div');t.id='updtoast';
 t.style.cssText='position:fixed;bottom:16px;left:16px;right:16px;z-index:99;background:var(--card2,#1a2238);border:1px solid var(--acc,#c9a24b);border-radius:14px;padding:12px 16px;display:flex;align-items:center;gap:12px;font-size:.85rem;box-shadow:0 8px 30px rgba(0,0,0,.4)';
 t.innerHTML='<span style="flex:1">نسخة جديدة من الموقع جاهزة</span><button id="upd-btn" style="min-height:40px;padding:0 16px;border:0;border-radius:10px;background:var(--acc,#c9a24b);color:var(--bg,#0b0f1a);font-weight:700;cursor:pointer">تحديث</button>';
 t.style.bottom='calc(16px + env(safe-area-inset-bottom,0px))';
 document.body.appendChild(t);
 t.querySelector('#upd-btn').onclick=()=>{
  const w=reg&&reg.waiting;
  if(w){w.postMessage('SKIP_WAITING')}
  let re=false;
  navigator.serviceWorker.addEventListener('controllerchange',()=>{if(!re){re=true;location.reload()}});
 };
}
/* local store: favorites / progress / continue / badges (P7) */
const store={
 k:'hc_store_v1',
 _d(){try{return JSON.parse(localStorage.getItem(this.k))||{}}catch(e){return{}}},
 _w(d){try{localStorage.setItem(this.k,JSON.stringify(d))}catch(e){}},
 get(sec,def){const d=this._d();return d[sec]!==undefined?d[sec]:def},
 set(sec,v){const d=this._d();d[sec]=v;this._w(d)},
 fav(rid){const d=this._d();d.fav=d.fav||{};return!!d.fav[rid]},
 favToggle(rid){const d=this._d();d.fav=d.fav||{};d.fav[rid]=!d.fav[rid];this._w(d);return d.fav[rid]},
 seen(key){const d=this._d();return(d.seen||{})[key]},
 markSeen(key){const d=this._d();d.seen=d.seen||{};d.seen[key]=Date.now();this._w(d)},
 resume(rid){const d=this._d();return(d.resume||{})[rid]},
 resumeList(){const d=this._d();const r=d.resume||{};return Object.keys(r).map(k=>({k:k,n:r[k].n,t:r[k].t})).sort((a,b)=>b.t-a.t)},
 favList(){const d=this._d();const f=d.fav||{};return Object.keys(f).filter(k=>f[k])},
 seenList(){const d=this._d();return Object.keys(d.seen||{})},
 setResume(rid,n){const d=this._d();d.resume=d.resume||{};d.resume[rid]={n:n,t:Date.now()};
  const ks=Object.keys(d.resume);if(ks.length>500){ks.sort((a,b)=>d.resume[a].t-d.resume[b].t);delete d.resume[ks[0]]}
  this._w(d)},
 export(){return JSON.stringify(this._d())},
 import_(s){try{const d=JSON.parse(s);if(typeof d==='object'){this._w(d);return true}}catch(e){}return false},
};
/* offline-save a row's texts + JSON into the pinned cache (hawshat-pinned-v1 — never LRU-trimmed) */
async function offlineRow(rowId,sSlug){
  if(!('caches' in window))return{ok:false,why:'caches'};
  try{
    if(navigator.storage&&navigator.storage.persist)navigator.storage.persist().catch(()=>{});
    const c=await caches.open('hawshat-pinned-v1');let n=0;
    const put=async u=>{try{
      if(await c.match(u))return 1;
      const r=await fetch(u);if(r.ok){await c.put(u,r);return 1}return 0
    }catch(e){return 0}};
    const rows=await(await fetch('data/read/'+encodeURIComponent(rowId)+'.json')).json();
    n+=await put('data/read/'+encodeURIComponent(rowId)+'.json');
    if(sSlug){
      n+=await put('series/'+encodeURIComponent(sSlug)+'.json');
      let li=null;
      try{const lr=await fetch('lessons/'+encodeURIComponent(sSlug)+'/index.json');if(lr.ok)li=await lr.json()}catch(e){}
      n+=await put('lessons/'+encodeURIComponent(sSlug)+'/index.json');
      const tf=(li&&li.tf)||{},af=(li&&li.af)||{};
      for(const k in tf)n+=await put('lessons/'+encodeURIComponent(sSlug)+'/'+tf[k]);
      for(const k in af)n+=await put('lessons/'+encodeURIComponent(sSlug)+'/'+af[k]);
    }
    for(const x of rows||[]){
      const u=x.base+encodeURIComponent(x.file);
      n+=await put(u);
    }
    const total=(rows||[]).length;
    return{ok:true,n:n,total:total,partial:false}
  }catch(e){return{ok:false,why:String(e)}}
}
async function isPinned(rowId){
  if(!('caches' in window))return false;
  try{return!!(await(await caches.open('hawshat-pinned-v1')).match('data/read/'+encodeURIComponent(rowId)+'.json'))}catch(e){return false}
}
/* toast / errState / emptyState — shared status components (D4) */
function toast(msg,ms){
  let t=document.getElementById('hctoast');
  if(!t){t=document.createElement('div');t.id='hctoast';document.body.appendChild(t)}
  t.textContent=msg;t.className='show';
  clearTimeout(t._h);t._h=setTimeout(()=>t.className='',ms||2200);
}
function errState(msg,retry){
  const off=navigator.onLine===false;
  return '<div class="errbox">'+esc(off?'لا اتصال — تفقد الشبكة ثم أعد المحاولة':msg)
    +(retry?' <button class="retry" onclick="'+retry+'">إعادة المحاولة</button>':'')+'</div>';
}
function emptyState(msg){return '<div class="empty">'+esc(msg)+'</div>'}
function fmtDur(s){
 if(typeof s==='string'&&/^\d{1,2}:\d{2}(:\d{2})?$/.test(s.trim())){
  const p=s.trim().split(':').map(Number);
  s=p.length===3?p[0]*3600+p[1]*60+p[2]:p[0]*60+p[1];
 }else s=Math.round(+s||0);
 if(!s)return'';
 const h=Math.floor(s/3600),m=Math.floor(s%3600/60),ss=s%60;
 return h?h+':'+String(m).padStart(2,'0')+':'+String(ss).padStart(2,'0'):m+':'+String(ss).padStart(2,'0');
}
function kfmt(n){n=+n||0;return n>999?((n/1000).toFixed(1).replace(/\.0$/,'')+'k'):String(n)}
