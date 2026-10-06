#!/usr/bin/env python3
"""crawl_site.py — visits EVERY sheikh, every row and every mode list of the
playlists site, then follows the first lesson of each mode. Fails on page
errors, HTTP >=400 on local files, error boxes, or empty lists.
Usage: python3 scripts/crawl_site.py   (serves the repo itself on :8899)"""
import asyncio,json,sys,os,threading,functools,http.server,socketserver
from playwright.async_api import async_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
B='http://localhost:8899/playlists/'
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
srv=socketserver.ThreadingTCPServer(('127.0.0.1',8899),functools.partial(Q,directory=ROOT))
threading.Thread(target=srv.serve_forever,daemon=True).start()
st=json.load(open(ROOT+'/playlists/data/sheikh_stats.json'))
MC={'read':'rdn','yt':'ytn','listen':'wan','qu':'qn','aud':None,'sm':'sun'}
jobs=[]
for s,v in st.items():
    if s=='_meta':continue
    jobs.append(('sheikh',s,'sheikh.html?s='+s))
    for r in v['rows']:
        jobs.append(('row',r['id'],'row.html?r='+r['id']))
        for m,k in MC.items():
            c=(r.get('ytn',0)+r.get('aun',0)) if m=='aud' else r.get(k,0)
            if c: jobs.append(('mode:'+m,r['id'],'row.html?r=%s&m=%s'%(r['id'],m)))
print('jobs',len(jobs),file=sys.stderr)
res=[]
async def worker(ctx,q):
    pg=await ctx.new_page()
    errs=[];bad=[]
    pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    pg.on('response',lambda r: bad.append(r.status) if r.status>=400 and 'localhost' in r.url and not r.url.endswith('.ico') else None)
    while q:
        kind,id_,u=q.pop()
        errs.clear();bad.clear()
        try:
            await pg.goto(B+u,wait_until='networkidle',timeout=45000)
            info=await pg.evaluate('''()=>({err:[...document.querySelectorAll('.errbox')].map(e=>e.textContent.slice(0,80)),
              empty:[...document.querySelectorAll('.empty')].map(e=>e.textContent.slice(0,60)),
              n:document.querySelectorAll('a.lrow,a.u-sr,.ltabs a').length,
              first:(document.querySelector('a.lrow')||{}).href||'' })''')
        except Exception as e:
            info={'err':['EXC '+str(e)[:80]],'empty':[],'n':0,'first':''}
        rec=dict(kind=kind,id=id_,u=u,pe=list(errs),bad=list(bad),**info)
        # follow first lesson link in mode pages
        if kind.startswith('mode:') and info['first']:
            errs.clear();bad.clear()
            try:
                await pg.goto(info['first'],wait_until='networkidle',timeout=45000)
                await pg.wait_for_timeout(300)
                i2=await pg.evaluate('''()=>({err:[...document.querySelectorAll('.errbox')].map(e=>e.textContent.slice(0,80)),
                  body:(document.querySelector('main')||document.body).innerText.length,
                  na:/غير متوفر|تعذر/.test(document.body.innerText)})''')
            except Exception as e: i2={'err':['EXC '+str(e)[:80]],'body':0,'na':True}
            rec['lesson']=dict(u=info['first'].replace(B,''),pe=list(errs),bad=list(bad),**i2)
        res.append(rec)
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(headless=True)
        ctx=await br.new_context(viewport={'width':390,'height':844},service_workers='block')
        await ctx.route('**/*youtube*/**',lambda r: r.abort())
        q=list(jobs)
        await asyncio.gather(*[worker(ctx,q) for _ in range(6)])
    fails=0
    for x in res:
        L=x.get('lesson') or {}
        p=[k for k,v in (('pageerror',x['pe']),('http',x['bad']),('errbox',x['err']),
            ('L-pageerror',L.get('pe')),('L-http',L.get('bad')),('L-errbox',L.get('err'))) if v]
        if x['kind']!='sheikh' and not x['n']:p.append('empty list')
        if p:fails+=1;print('FAIL',x['u'],L.get('u',''),p,(x['pe']+(L.get('pe') or []))[:1])
    print('crawl_site: %d fails / %d pages'%(fails,len(res)))
    sys.exit(1 if fails else 0)
asyncio.run(main())
