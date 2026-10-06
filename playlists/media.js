/* media.js — YouTube video + audio-only player used by d.html.
   Audio-only = a 1px live YouTube iframe driven by our own controls (display:none
   makes YouTube pause), with lock-screen controls through MediaSession. */
const HM=(()=>{
  const EMB='https://www.youtube-nocookie.com/embed/';
  const embed=(v,ap)=>EMB+encodeURIComponent(v)+'?playsinline=1&rel=0&hl=ar&iv_load_policy=3&modestbranding=1'+(ap?'&autoplay=1':'');
  const thumb=v=>'https://i.ytimg.com/vi/'+encodeURIComponent(v)+'/hqdefault.jpg';
  let _api=null;
  const api=()=>_api||(_api=new Promise(res=>{
    const pv=window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady=()=>{if(pv)pv();res(window.YT)};
    const s=document.createElement('script');s.src='https://www.youtube.com/iframe_api';
    s.onerror=()=>res(null);document.head.appendChild(s)}));
  const t=s=>{s=Math.max(0,Math.floor(s||0));const h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;
    return h?h+':'+String(m).padStart(2,'0')+':'+String(x).padStart(2,'0'):m+':'+String(x).padStart(2,'0')};
  const SP=[0.75,1,1.25,1.5,1.75,2];
  /* audio-only player; returns {destroy}. el gets the whole UI. */
  function audio(el,o){
    const ic=i=>'<svg class="i"><use href="icons.svg?v=12#'+i+'"/></svg>';
    let si=Math.max(0,SP.indexOf(+store.get('aspd',1)));if(si<0)si=1;
    el.innerHTML='<div class="ap" role="group" aria-label="مشغّل الصوت">'
      +'<div class="ap-ph"><div id="apy"></div></div>'
      +'<div class="ap-bar" id="apb" role="slider" aria-label="موضع التشغيل" tabindex="0"><i id="apf"></i></div>'
      +'<div class="ap-tm"><span id="apc">0:00</span><span id="aps" class="ap-st">جارٍ التحميل…</span><span id="apd">0:00</span></div>'
      +'<div class="ap-ct">'
      +'<button id="apsp" class="ap-sp" aria-label="سرعة التشغيل">×'+SP[si]+'</button>'
      +'<button id="apbk" aria-label="رجوع 10 ثوانٍ">'+ic('i-rew10')+'</button>'
      +'<button id="appl" class="ap-pl" aria-label="تشغيل">'+ic('i-play')+'</button>'
      +'<button id="apfw" aria-label="تقديم 10 ثوانٍ">'+ic('i-fwd10')+'</button>'
      +'<a class="ap-ext" href="https://youtu.be/'+encodeURIComponent(o.vid)+'" target="_blank" rel="noopener" aria-label="افتح على يوتيوب">'+ic('i-ext')+'</a>'
      +'</div></div>';
    const G=id=>el.querySelector('#'+id);let P=null,dead=false,playing=false;
    const pos=store.get('apos:'+o.key);
    const up=()=>{if(!P||dead||!P.getDuration)return;try{const d=P.getDuration()||0,c=P.getCurrentTime()||0;
      G('apc').textContent=t(c);G('apd').textContent=t(d);G('apf').style.width=(d?Math.min(100,c/d*100):0)+'%';
      if(playing&&c>5)store.set('apos:'+o.key,{c:Math.floor(c),d:Math.floor(d)})}catch(e){}};
    const tm=setInterval(up,500);
    const st=s=>{const e=G('aps');if(e)e.textContent=s};
    api().then(YT=>{if(dead)return;if(!YT){st('تعذر الاتصال بيوتيوب');return}
      P=new YT.Player(G('apy'),{videoId:o.vid,playerVars:{autoplay:o.autoplay?1:0,controls:0,playsinline:1,rel:0,disablekb:1,fs:0,iv_load_policy:3,hl:'ar',
        start:(pos&&pos.d&&pos.c<pos.d-15)?pos.c:0},
        events:{onReady:()=>{try{P.setPlaybackRate(SP[si])}catch(e){}st(o.autoplay?'':'جاهز');up()},
          onStateChange:e=>{if(dead)return;playing=e.data===1;
            G('appl').innerHTML=ic(playing?'i-pause':'i-play');G('appl').setAttribute('aria-label',playing?'إيقاف مؤقت':'تشغيل');
            st({1:'',2:'متوقف',3:'تحميل…',0:'انتهى'}[e.data]??'');
            if(e.data===0){store.set('apos:'+o.key,null);o.onEnd&&o.onEnd()}up()},
          onError:()=>st('تعذر التشغيل — افتح على يوتيوب')}})});
    G('appl').onclick=()=>{if(P)playing?P.pauseVideo():P.playVideo()};
    const sk=d=>{try{P.seekTo(Math.max(0,P.getCurrentTime()+d),true)}catch(e){}};
    G('apbk').onclick=()=>sk(-10);G('apfw').onclick=()=>sk(10);
    G('apsp').onclick=()=>{si=(si+1)%SP.length;store.set('aspd',SP[si]);G('apsp').textContent='×'+SP[si];try{P.setPlaybackRate(SP[si])}catch(e){}};
    const seek=x=>{try{const r=G('apb').getBoundingClientRect(),d=P.getDuration()||0;
      if(d)P.seekTo(d*Math.min(1,Math.max(0,(r.right-x)/r.width)),true)}catch(e){}};
    G('apb').onclick=e=>seek(e.clientX);
    G('apb').onkeydown=e=>{if(e.key==='ArrowLeft')sk(10);if(e.key==='ArrowRight')sk(-10)};
    if('mediaSession' in navigator){try{
      navigator.mediaSession.metadata=new MediaMetadata({title:o.title,artist:o.artist||'',album:o.album||'سلاسل المشايخ',
        artwork:[{src:thumb(o.vid),sizes:'480x360',type:'image/jpeg'}]});
      const ms=(a,f)=>{try{navigator.mediaSession.setActionHandler(a,f)}catch(e){}};
      ms('play',()=>P&&P.playVideo());ms('pause',()=>P&&P.pauseVideo());
      ms('seekbackward',()=>sk(-10));ms('seekforward',()=>sk(10));
      ms('previoustrack',o.onPrev||null);ms('nexttrack',o.onNext||null);
    }catch(e){}}
    return {destroy(){dead=true;clearInterval(tm);try{P&&P.destroy()}catch(e){}el.innerHTML=''},
      toggle(){G('appl').click()}};
  }
  return {embed,thumb,audio,fmt:t};
})();
