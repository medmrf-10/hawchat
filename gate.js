/* بوابة كلمة السر — قفل ناعم على الصفحات */
(function(){
 if(/lock\.html/.test(location.pathname))return;
 try{if(localStorage.getItem('hwk')==='1')return}catch(e){}
 var s=(document.currentScript&&document.currentScript.src)||'';
 var root=s.replace(/gate\.js.*$/,'');
 location.replace(root+'lock.html?b='+encodeURIComponent(location.pathname+location.search));
})();
