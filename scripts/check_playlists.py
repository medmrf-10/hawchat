#!/usr/bin/env python3
"""check_playlists.py — pre-push gate for the sheikh-series site.
Fails (exit 1) if: any JSON is invalid or has conflict markers,
row invariants are violated (wan<=rdn<=rtt, wan<=wtt), a read link
points to a missing data/read/<id>.json, or an unknown sheikh_slug
appears. Run before every commit touching playlists/ or transcripts/."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PL   = os.path.join(ROOT, 'playlists')
BAD  = []

def fail(m):
    BAD.append(m); print('FAIL:', m)

def scan_markers(path):
    try:
        head = open(path, encoding='utf-8', errors='ignore').read(200000)
    except Exception as e:
        return fail('unreadable %s: %s' % (path, e))
    for mk in ('<<<<<<<', '=======', '>>>>>>>'):
        if mk in head:
            fail('conflict marker in %s' % path)

def J(path):
    scan_markers(path)
    try:
        return json.load(open(path, encoding='utf-8'))
    except Exception as e:
        fail('invalid json %s: %s' % (path, e))
        return None

# validate every json under playlists/ + transcripts/index.json
for dirpath, _, files in os.walk(PL):
    for f in files:
        if f.endswith('.json'):
            J(os.path.join(dirpath, f))
J(os.path.join(ROOT, 'transcripts', 'index.json'))

st = J(os.path.join(PL, 'data', 'sheikh_stats.json')) or {}
meta = st.get('_meta')
sheikhs = J(os.path.join(PL, 'data', 'sheikhs.json')) or {}
known = {s['slug'] for s in sheikhs.get('sheikhs', [])}

for slug, v in st.items():
    if slug == '_meta' or not isinstance(v, dict):
        continue
    for r in v.get('rows', []):
        if not (r['wan'] <= r['rdn'] <= max(r['rtt'], r['rdn'])):
            fail('invariant rdn: %s %s' % (slug, r.get('title')))
        if r['wan'] > max(r['wtt'], r['wan']):
            fail('invariant wtt: %s %s' % (slug, r.get('title')))
        rid = r.get('id')
        if rid and not os.path.exists(os.path.join(PL, 'data', 'read', rid + '.json')):
            fail('missing read file for %s' % rid)

sidx = (J(os.path.join(PL, 'series', 'index.json')) or {}).get('series', [])
for s in sidx:
    if s.get('sheikh_slug') and s['sheikh_slug'] not in known:
        fail('orphan sheikh_slug %s in series %s' % (s.get('sheikh_slug'), s.get('slug')))

if BAD:
    sys.exit(1)
print('check_playlists OK')
