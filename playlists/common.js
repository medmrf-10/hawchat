/* common.js — shared helpers for سلاسل المشايخ */
function esc(s){return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function j(u){try{const r=await fetch(u,{cache:'no-cache'});return r.ok?await r.json():null}catch(e){return null}}
async function jtxt(u){try{const r=await fetch(u);return r.ok?await r.text():null}catch(e){return null}}
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
