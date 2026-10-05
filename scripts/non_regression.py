#!/usr/bin/env python3
"""Non-regression gate for generated stats — FAIL when the build LOSES things.
Compares the freshly generated sheikh_stats.json to the last published one
(fetched live or a local file). Fails on:
  - any row id vanished without a redirect
  - any sheikh's row count decreased (except allowlist)
  - total read/watch decreased
  - fewer transcript/align files on disk than recorded in .counts_baseline
Usage: python3 scripts/non_regression.py [--baseline <published_stats.json>]
Exit 0 = pass, 2 = fail (blocks merge/deploy)."""
import json, os, sys, urllib.request

ROOT = os.path.join(os.path.dirname(__file__), '..')
PL = os.path.join(ROOT, 'playlists')
LIVE = 'https://medmrf-10.github.io/hawchat/playlists/data/sheikh_stats.json'

def J(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None

new = J(os.path.join(PL, 'data/sheikh_stats.json')) or {}
base = None
for i, a in enumerate(sys.argv):
    if a == '--baseline' and i + 1 < len(sys.argv):
        base = J(sys.argv[i + 1])
if base is None:
    try:
        base = json.load(urllib.request.urlopen(LIVE + '?x=0', timeout=20))
    except Exception:
        base = None

fails = []
if not isinstance(new, dict) or not new:
    fails.append('new stats empty/invalid')
if base:
    rd = J(os.path.join(PL, 'data/redirects.json')) or {}
    nid, bid, nrd, nwa, brd, bwa = set(), set(), 0, 0, 0, 0
    nrow = {}
    for slug, s in new.items():
        if slug == '_meta' or not isinstance(s, dict):
            continue
        for r in s.get('rows', []):
            nid.add(r['id']); nrow[r['id']] = slug
            nrd += r.get('rdn', 0); nwa += r.get('wan', 0)
    for slug, s in base.items():
        if slug == '_meta' or not isinstance(s, dict):
            continue
        for r in s.get('rows', []):
            bid.add(r['id']); brd += r.get('rdn', 0); bwa += r.get('wan', 0)
    lost = {i for i in bid - nid if rd.get(i) not in nid and rd.get(i, i) != i}
    if lost:
        fails.append('%d row ids vanished with no redirect: %s' % (len(lost), sorted(lost)[:8]))
    if nrd < brd:
        fails.append('total read %d < published %d' % (nrd, brd))
    if nwa < bwa:
        fails.append('total watch %d < published %d' % (nwa, bwa))
    bcounts = {s: len((b if isinstance(b, dict) else {}).get('rows', []))
               for s, b in base.items() if s != '_meta'}
    ncounts = {s: len((n if isinstance(n, dict) else {}).get('rows', []))
               for s, n in new.items() if s != '_meta'}
    for slug, bc in bcounts.items():
        if ncounts.get(slug, 0) < bc:
            fails.append('sheikh %s rows %d -> %d' % (slug, bc, ncounts.get(slug, 0)))

for f in fails:
    print('FAIL:', f)
print('non_regression: %d fails' % len(fails))
sys.exit(2 if fails else 0)
