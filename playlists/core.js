/* core.js — single source of truth for: which row a URL means, which lessons
   it has, what each lesson offers (watch/read/yt/audio/summary/questions) and
   the link to each. Every page uses this instead of its own copy. */
const HC=(()=>{
  const MODES=[['listen','i-watch','مشاهدة حية'],['read','i-read','قراءة'],['yt','i-yt','يوتيوب'],
               ['aud','i-audio','استماع'],['sm','i-list','ملخص'],['qu','i-qu','أسئلة']];
  const PRI=['listen','read','yt','aud','sm','qu'];
  let _st=null,_red;
  const stats=async()=>_st||(_st=await j('data/sheikh_stats.json'));
  const okVid=v=>!!(v&&String(v).length>=8);
  async function findRow(q){
    const st=await stats();if(!st)return null;
    const hit=p=>{for(const s in st){if(s==='_meta')continue;
      const r=(st[s].rows||[]).find(p);if(r)return{r,slug:s,st:st[s]}}return null};
    let rid=q.get('r'),h=rid?hit(r=>r.id===rid):null;
    if(!h&&rid){if(_red===undefined)_red=await j('data/redirects.json')||{};
      if(_red[rid])h=hit(r=>r.id===_red[rid])}
    const s=q.get('s')||q.get('k');
    if(!h&&s&&!q.get('sh'))h=hit(r=>r.sSlug===s)||hit(r=>r.id===s);
    if(!h&&q.get('id'))h=hit(r=>String(r.mutId)===String(q.get('id')));
    if(!h&&q.get('sh'))h=hit(r=>r.trSh===q.get('sh')&&r.trSr===q.get('s'));
    return h;
  }
  const _lc=new Map();
  function lessons(row){
    if(!_lc.has(row.id))_lc.set(row.id,_lessons(row));
    return _lc.get(row.id);
  }
  async function _lessons(row){
    const ld=row.ld??row.sSlug;
    const [sd,li,rd,ax]=await Promise.all([
      row.sSlug?j('series/'+encodeURIComponent(row.sSlug)+'.json'):null,
      ld?j('lessons/'+encodeURIComponent(ld)+'/index.json'):null,
      row.rdn?j('data/read/'+encodeURIComponent(row.id)+'.json'):null,
      (row.aun||!row.sSlug)?j('audio/index.json'):null]);
    const akey=row.sSlug||row.id;
    const au=new Map((((ax||{})[akey]||{}).items||[]).map(a=>[a.n,a]));
    const S=k=>new Set((li&&li[k])||[]);
    const aln=new Set((li&&(li.alignOk||li.align))||[]),smn=S('sum'),qun=S('qu'),txn=S('txt');
    const ti=(li&&li.ti)||{};
    const rx=new Map((rd||[]).map(x=>[x.n,x]));
    const sl=new Map(((sd&&sd.lessons)||[]).map(l=>[l.n,l]));
    const ns=new Set([...aln,...txn,...rx.keys(),...au.keys()]);
    for(const l of sl.values())if(okVid(l.video))ns.add(l.n);
    const list=[];
    for(const n of ns){
      const l=sl.get(n)||{},x=rx.get(n)||{};
      const vid=okVid(l.video)?l.video:(okVid(x.vid)?x.vid:'');
      const has={listen:!!(row.sSlug&&aln.has(n)),read:txn.has(n)||rx.has(n),yt:!!vid,
        aud:!!vid||au.has(n),sm:smn.has(n),qu:qun.has(n)};
      list.push({n,title:cleanTitle(ti[n]||x.title||l.title||'',n,row)||('الدرس '+n),
        dur:l.dur||0,vid,sv:okVid(l.video),au:au.get(n),has});
    }
    list.sort((a,b)=>(ordOf(a.title)||a.n)-(ordOf(b.title)||b.n));
    // «العلمانية هي الحل» ×3 in a row = one talk in parts — say so instead of repeating
    for(let i=0;i<list.length;){let k=i;while(k+1<list.length&&list[k+1].title===list[i].title)k++;
      if(k>i)for(let p=i;p<=k;p++){list[p].part=p-i+1;list[p].parts=k-i+1}i=k+1}
    return {row,list,by:new Map(list.map(x=>[x.n,x])),akey,li,rx,ld};
  }
  const ORD={'الأول':1,'الثاني':2,'الثالث':3,'الرابع':4,'الخامس':5,'السادس':6,'السابع':7,'الثامن':8,'التاسع':9,'العاشر':10,'الحادي':1,'العشرون':20,'الثلاثون':30,'الأربعون':40,'الخمسون':50,'الستون':60,'السبعون':70,'الثمانون':80,'التسعون':90,'المائة':100};
  // «الدرس السادس» in the title outranks upload order (n)
  function ordOf(t){
    if(!t)return 0;
    let m=t.match(/الدرس\s+(?:ال)?(\d+)/);if(m)return +m[1];
    m=t.match(/الدرس\s+ال([أ-ي\s]+?)(?:\s|$|—|-|\()/);
    if(m){let s=0,ok=0;for(const x of m[1].trim().split(/\s+/).map(x=>x.replace(/^و/,'')))if(ORD[x]){s+=ORD[x];ok=1}
      if(ok)return s}
    return 0;
  }
  // titles carry «series — sheikh | #hashtag» boilerplate and a repeated number
  function cleanTitle(t,n,row){
    let s=String(t||'');
    s=s.replace(/\s*[(\[]?\s*[Ww]ith [Ee]nglish [Tt]ranslation\s*[)\]]?\s*/g,'').replace(/#[\p{L}\p{N}_]+/gu,' ').replace(/⧵|：/g,' — ');
    // the list shows n in its own badge — a leading «12-» / «3:» is noise
    s=s.replace(/^\s*[\d٠-٩]{1,4}\s*[-–—:|.)]\s*/,'');
    if(row)for(const strip of [row.title,row._sname]){if(!strip||strip.length<4)continue;
      const r2=s.split(strip).join('').replace(/^[\s|｜:—–-]+|[\s|｜:—–-]+$/g,'');if(r2.length>=4)s=r2}
    return s.replace(/(\s*[|｜]\s*)+$/,'').replace(/^(\s*[|｜:]\s*)+/,'').replace(/\s{2,}/g,' ').replace(/^[\s—–-]+|[\s—–-]+$/g,'').trim();
  }
  /* one lesson page (d.html) for read/video/audio/summary/questions; the
     word-synced player (lesson.html) stays separate — it is its own instrument */
  function href(ctx,x,m){
    const row=ctx.row,id=encodeURIComponent(row.id),n=x.n;
    if(m==='listen')return 'lesson.html?s='+encodeURIComponent(row.sSlug||'')+'&l='+n;
    return 'd.html?r='+id+'&l='+n+(m?'&t='+m:'');
  }
  // the lesson's door: the requested mode if it has it, else the richest one
  function best(x,want){
    if(want&&x.has[want])return want;
    return PRI.find(k=>x.has[k])||null;
  }
  function remember(rowId,n,m,title,rowTitle){
    const d=store._d();d.hist=(d.hist||[]).filter(h=>h.r!==rowId);
    d.hist.unshift({r:rowId,n,m,ti:title||'',rt:rowTitle||'',t:Date.now()});d.hist=d.hist.slice(0,30);
    d.seen=d.seen||{};d.seen[rowId+':'+n]=Date.now();
    store._w(d);
  }
  const _ic=id=>'<svg class="i"><use href="icons.svg?v=11#'+id+'"/></svg>';
  /* lesson pages: a tab strip that switches mode for the SAME lesson */
  async function mountTabs(active){
    try{
      const q=new URLSearchParams(location.search);
      const hit=await findRow(q);if(!hit)return;
      const ctx=await lessons(hit.r);
      const n=parseInt(q.get('l')||q.get('n'),10)||(ctx.list[0]&&ctx.list[0].n);
      const x=ctx.by.get(n);if(!x)return;
      remember(hit.r.id,n,active,x.title,hit.r.title);
      let bar=document.getElementById('ltabs');
      if(!bar){bar=document.createElement('nav');bar.id='ltabs';bar.className='ltabs';bar.setAttribute('aria-label','طريقة عرض الدرس');
        const hd=document.querySelector('header.hd');hd?hd.after(bar):document.body.prepend(bar)}
      const avail=MODES.filter(([k])=>x.has[k]);
      if(avail.length<2){bar.hidden=true;return}
      bar.hidden=false;
      bar.innerHTML='<div class="ltabs-in">'+avail.map(([k,i,a])=>k===active
        ?'<span class="lt on" aria-current="page">'+_ic(i)+'<span>'+a+'</span></span>'
        :'<a class="lt" href="'+href(ctx,x,k)+'">'+_ic(i)+'<span>'+a+'</span></a>').join('')+'</div>';
    }catch(e){}
  }
  // pages that switch lesson in place (pushState) keep their tabs in sync
  function follow(active){
    for(const f of ['pushState','replaceState']){const o=history[f];
      history[f]=function(){const r=o.apply(this,arguments);mountTabs(active);return r}}
    addEventListener('popstate',()=>mountTabs(active));
  }
  const partOf=x=>x.parts?'الجزء '+x.part+' من '+x.parts:'';
  return {partOf,MODES,PRI,stats,findRow,lessons,href,best,remember,mountTabs,follow,cleanTitle,ordOf};
})();
