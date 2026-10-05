#!/usr/bin/env python3
"""Full-site consistency audit for playlists/: every card row must resolve.
Checks per sheikh/row: read-file exists+nonempty+count==rdn, listen link → series json +
lessons index align==wan, card leads to ≥1 row, stats invariants, JSON validity.
Exit 1 on any FAIL. Usage: python3 scripts/audit_site.py [root]"""
import json, os, re, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..')
PL = os.path.join(ROOT, 'playlists')
fails, warns = [], []

def J(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception as e:
        fails.append('invalid json %s: %s' % (p, e)); return None

st = J(os.path.join(PL, 'data/sheikh_stats.json')) or {}
for slug, s in st.items():
    if slug == '_meta' or not isinstance(s, dict):
        continue
    rows = s.get('rows') or []
    if s.get('read', 0) + s.get('watch', 0) > 0 and not rows:
        fails.append('%s: counters>0 but no rows' % slug)
    for r in rows:
        rid = r.get('id')
        if not rid:
            fails.append('%s: row without id %r' % (slug, r.get('title'))); continue
        if not (0 <= r.get('wan', 0) <= r.get('rdn', 0) <= r.get('rtt', 0) and r['wan'] <= r.get('wtt', 0)):
            fails.append('%s/%s: invariant wan<=rdn<=rtt broken (%s/%s/%s)' % (slug, rid, r['wan'], r['rdn'], r['rtt']))
        if r.get('read') and not r['read'].startswith('tr.html?r='):
            fails.append('%s/%s: read link not tr.html' % (slug, rid))
        if r.get('listen') and r.get('wan', 0) <= 0:
            fails.append('%s/%s: listen link with wan=0' % (slug, rid))
        if r.get('wan', 0) > 0 and not r.get('listen'):
            fails.append('%s/%s: wan>0 but no listen link' % (slug, rid))
        # read file
        rp = os.path.join(PL, 'data/read', rid + '.json')
        if not os.path.exists(rp):
            fails.append('%s/%s: missing read file' % (slug, rid))
        else:
            rd = J(rp)
            if rd is not None:
                if not rd and r.get('rdn', 0) > 0:
                    fails.append('%s/%s: read file empty but rdn=%d' % (slug, rid, r['rdn']))
                elif rd and abs(len(rd) - r.get('rdn', 0)) > 0:
                    warns.append('%s/%s: read file %d rows vs rdn %d' % (slug, rid, len(rd), r['rdn']))
        # listen truth
        if r.get('sSlug') and r.get('wan', 0) > 0:
            sp = os.path.join(PL, 'series', r['sSlug'] + '.json')
            if not os.path.exists(sp):
                fails.append('%s/%s: listen but missing series/%s.json' % (slug, rid, r['sSlug']))
            lp = os.path.join(PL, 'lessons', r['sSlug'], 'index.json')
            li = J(lp) if os.path.exists(lp) else None
            if li is None:
                fails.append('%s/%s: listen but no lessons index' % (slug, rid))
            elif len(li.get('align') or []) != r['wan']:
                warns.append('%s/%s: align %d vs wan %d' % (slug, rid, len(li.get('align') or []), r['wan']))

for w in warns: print('WARN', w)
for f in fails: print('FAIL', f)
print('audit_site: %d fails %d warns' % (len(fails), len(warns)))
sys.exit(1 if fails else 0)
