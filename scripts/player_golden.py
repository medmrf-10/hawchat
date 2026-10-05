#!/usr/bin/env python3
"""player_golden.py — golden baseline for lesson.html's proven player logic.
Serves the repo locally, fakes the YouTube Iframe API with a controllable clock,
drives 30 timestamps per lesson, and records (curPh, curW, phrase text).
Baseline mode saves golden.json; --check compares a run to the saved baseline.
Usage: python3 scripts/player_golden.py            # write baseline
      python3 scripts/player_golden.py --check    # compare vs baseline"""
import json, os, sys, threading, functools, http.server, socketserver, subprocess, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GOLD = os.path.join(ROOT, 'scripts', 'player_golden.json')
PORT = 8877
LESSONS = [('bouti-sira', 1), ('bouti-aqeeda', 1), ('gomaa-khawarij', 45), ('hashimi-zawaj', 1), ('bouti-tarikh', 1)]
TIMES = [0, 5, 15, 30, 60, 90, 120, 180, 240, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3600, 4000]

FAKE_YT = r"""window.__t=0;window.__seeks=[];
window.YT={PlayerState:{PLAYING:1,PAUSED:2,ENDED:0},
Player:function(id,cfg){var self=this;this._cfg=cfg||{};
 setTimeout(function(){cfg.events&&cfg.events.onReady&&cfg.events.onReady({target:self})},50);
 this.getCurrentTime=function(){return window.__t};
 this.seekTo=function(s){window.__t=s;window.__seeks.push(s)};
 this.playVideo=function(){this._st=1};this.pauseVideo=function(){this._st=2};
 this.getPlayerState=function(){return this._st||1};this._st=1;
}};
window.onYouTubeIframeAPIReady&&window.onYouTubeIframeAPIReady();
"""

def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    class Q(socketserver.TCPServer):
        allow_reuse_address = True
        def log_message(self, *a): pass
    srv = Q(('127.0.0.1', PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

def main(check=False):
    srv = serve()
    from playwright.sync_api import sync_playwright
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path='/home/ubuntu/.local/bin/google-chrome' if os.path.exists('/home/ubuntu/.local/bin/google-chrome') else None, headless=True)
        pg = br.new_page()
        # routes match in reverse registration order — register the
        # catch-all FIRST so the iframe_api fake takes precedence.
        pg.route('**/www.youtube.com/**', lambda rt: rt.fulfill(body='', content_type='text/html'))
        pg.route('**/iframe_api', lambda rt: rt.fulfill(body=FAKE_YT, content_type='application/javascript'))
        for slug, n in LESSONS:
            key = '%s/%d' % (slug, n)
            url = 'http://127.0.0.1:%d/playlists/lesson.html?s=%s&l=%d' % (PORT, slug, n)
            recs = []
            try:
                pg.goto(url, wait_until='domcontentloaded', timeout=15000)
                pg.wait_for_timeout(2500)
                recs = pg.evaluate("""async (times)=>{
                  const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));
                  const out=[];
                  for (const t of times){
                    window.__t=t; await sleep(220);
                    const on=document.querySelector('#stage .w.on, .ph .w.on');
                    const pos=document.querySelector('#pos');
                    out.push([t, {ph: (typeof curPh!=='undefined'?curPh:null),
                              w: (typeof curW!=='undefined'?curW:null),
                              pos: pos?pos.textContent:null,
                              word: on?on.textContent:null,
                              seeks: window.__seeks.slice()}]);
                  }
                  return out;}""", TIMES)
                out[key] = recs
            except Exception as e:
                out[key] = 'ERROR: %s' % str(e)[:120]
        br.close()
    srv.shutdown()
    if not check:
        json.dump(out, open(GOLD, 'w'), ensure_ascii=False)
        print('baseline written →', GOLD)
        return 0
    gold = json.load(open(GOLD))
    bad = []
    for k, recs in out.items():
        g = gold.get(k)
        if g is None or g != recs:
            if isinstance(recs, str):
                bad.append('%s %s' % (k, recs))
            else:
                diffs = [(t, recs[i][1] != (g[i][1] if i < len(g) else None)) for i, (t, _) in enumerate(recs)]
                nd = sum(1 for _, d in diffs if d)
                bad.append('%s: %d/%d timestamps differ' % (k, nd, len(recs)))
    for b in bad: print('DIFF', b)
    print('golden: %s' % ('MATCH' if not bad else '%d differences' % len(bad)))
    return 0 if not bad else 1

if __name__ == '__main__':
    sys.exit(main(check='--check' in sys.argv))
