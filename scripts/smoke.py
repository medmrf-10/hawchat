#!/usr/bin/env python3
"""smoke.py — Playwright smoke test for the playlists site.
Visits key pages at mobile+desktop sizes; FAILS on console errors,
requests >=400, horizontal overflow, tap targets <44px, [hidden] visible.
Usage: python3 scripts/smoke.py [base_url]   (default: live site)
      python3 scripts/smoke.py http://localhost:8000/   (local)"""
import json, os, sys, urllib.request

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'https://medmrf-10.github.io/hawchat/playlists'
ROOT = os.path.join(os.path.dirname(__file__), '..')
PL = os.path.join(ROOT, 'playlists')

st = json.load(open(os.path.join(PL, 'data/sheikh_stats.json')))
one_sh = next(k for k, s in st.items() if isinstance(s, dict) and s.get('rows'))
one_row = next(r for s in st.values() if isinstance(s, dict) for r in s.get('rows', []) if r.get('read'))
one_listen = next((r for s in st.values() if isinstance(s, dict) for r in s.get('rows', []) if r.get('listen')), None)

pages = [BASE + '/', BASE + '/index.html', BASE + '/sheikh.html?s=' + one_sh,
         BASE + '/' + one_row['read'],
         BASE + '/tr.html?r=' + one_row['id'] + '&l=1']
if one_listen:
    pages += [BASE + '/' + one_listen['listen'],
              BASE + '/lesson.html?s=' + one_listen['sSlug'] + '&l=1']

results = []
def run():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path='/home/ubuntu/.local/bin/google-chrome' if os.path.exists('/home/ubuntu/.local/bin/google-chrome') else None,
                                headless=True, args=['--disable-http2'])
        for vw in ((360, 740), (1280, 800)):
            pg = br.new_page(viewport={'width': vw[0], 'height': vw[1]})
            errs, bad_req = [], []
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            pg.on('response', lambda r: bad_req.append('%s %s' % (r.status, r.url[-80:])) if r.status >= 400 else None)
            for url in pages:
                errs.clear(); bad_req.clear()
                try:
                    pg.goto(url, wait_until='domcontentloaded', timeout=20000)
                    pg.wait_for_timeout(3500)
                except Exception as e:
                    results.append(('FAIL', url, str(e)[:100])); continue
                met = pg.evaluate("""() => ({
                    sw: document.documentElement.scrollWidth, vw: innerWidth,
                    smallTap: [...document.querySelectorAll('a,button,[role=button],input,select')]
                        .filter(el => el.offsetParent && !el.closest('p, .txtbody'))
                        .map(el => el.getBoundingClientRect())
                        .filter(rc => rc.width > 0 && (rc.height < 43 || rc.width < 43)).length,
                    hiddenShown: [...document.querySelectorAll('[hidden]')]
                        .filter(el => getComputedStyle(el).display !== 'none').length,
                })""")
                probs = []
                if errs: probs.append('console: ' + errs[0][:80])
                if bad_req: probs.append('%d req>=400 e.g. %s' % (len(bad_req), bad_req[0]))
                if met['sw'] > met['vw'] + 2: probs.append('horizontal overflow %d>%d' % (met['sw'], met['vw']))
                if met['hiddenShown']: probs.append('%d [hidden] still displayed' % met['hiddenShown'])
                if met['smallTap']: probs.append('%d tap targets <44px' % met['smallTap'])
                results.append(('FAIL' if probs else 'ok', '%dx%d %s' % (vw[0], vw[1], url.split('playlists')[-1]), '; '.join(probs)))
            pg.close()
        br.close()

try:
    run()
except Exception as e:
    print('smoke harness error:', e); sys.exit(2)

for st_, url, why in results:
    print(st_, url, why)
fails = sum(1 for r in results if r[0] == 'FAIL')
print('smoke: %d fails / %d checks' % (fails, len(results)))
sys.exit(1 if fails else 0)
