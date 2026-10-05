#!/usr/bin/env python3
"""gen_stats.py — rebuild playlists/data/sheikh_stats.json.
Single source of truth for BOTH the index cards and sheikh pages:
per-sheikh rows {title, rdn (readable lessons), rtt, wan (aligned), wtt,
kind, mutId/trSh/trSr/sSlug} plus totals. Reads only site data files."""
import json, os, re, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))          # playlists/data
PL   = os.path.dirname(BASE)                                # playlists
ROOT = os.path.dirname(PL)                                  # hawchat root

def J(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None

def norm(s):
    s = re.sub(r'[\u064B-\u0652\u0670]', '', s or '')
    return re.sub(r'[^\w\s]', '', s).strip()

def fetch(u):
    try:
        return json.load(urllib.request.urlopen(u, timeout=20))
    except Exception:
        return None

sheikhs = (J(os.path.join(PL, 'data/sheikhs.json')) or {}).get('sheikhs', [])
sidx    = (J(os.path.join(PL, 'series/index.json')) or {}).get('series', [])
tr      = (J(os.path.join(ROOT, 'transcripts/index.json')) or {}).get('sheikhs', {})
man     = fetch('https://medmrf-10.github.io/des/mutalaa/data/manifest.json') or {}
muts    = man if isinstance(man, list) else man.get('series', [])

out = {}
for sh in sheikhs:
    slug = sh['slug']
    nset = set()
    for x in [sh.get('name_display'), sh.get('name')] + (sh.get('aliases') or []):
        if x:
            nset.add(x); nset.add(norm(x))
    rows = []
    def hit(title):
        st = norm(title)
        for r in rows:
            rt = norm(r['title'])
            if rt and (rt in st or st in rt):
                return r
        return None
    for m in muts:
        if not (nset & {m.get('sheikh'), norm(m.get('sheikh') or '')}):
            continue
        if (m.get('done') or 0) <= 0 and not m.get('files'):
            continue
        rdn = m.get('done') or len(m.get('files') or [])
        rtt = m.get('total') or rdn
        rows.append({'title': m.get('name') or m.get('title') or ('#' + str(m.get('id'))),
                     'rdn': rdn, 'rtt': rtt, 'wan': 0, 'wtt': 0,
                     'kind': 'mut', 'mutId': m.get('id')})
    for s in sidx:
        if s.get('sheikh_slug') != slug:
            continue
        if (s.get('aligned') or 0) <= 0 and (s.get('transcribed') or 0) <= 0:
            continue
        r = hit(s.get('title') or '')
        if not r:
            r = {'title': s.get('title'), 'rdn': 0, 'rtt': 0, 'wan': 0, 'wtt': 0, 'kind': None}
            rows.append(r)
        if (s.get('aligned') or 0) > 0:
            r['wan'] = s['aligned']; r['wtt'] = s.get('count') or s['aligned']
            r['sSlug'] = s['slug']
        if (s.get('transcribed') or 0) > 0 and not r['rdn']:
            r['rdn'] = s['transcribed']; r['rtt'] = s.get('count') or s['transcribed']
            if not r['kind']:
                r['kind'] = 's'; r['sSlug'] = s['slug']
    for k, v in tr.items():
        if (v.get('slug') or k) != slug:
            continue
        for sr in (v.get('series') or []):
            r = hit(sr.get('title') or '')
            if not r:
                r = {'title': sr.get('title'), 'rdn': 0, 'rtt': 0, 'wan': 0, 'wtt': 0, 'kind': None}
                rows.append(r)
            if not r['rdn']:
                r['rdn'] = sr.get('n') or len(sr.get('files') or [])
                r['rtt'] = sr.get('total') or r['rdn']
                if not r['kind']:
                    r['kind'] = 'tr'; r['trSh'] = k; r['trSr'] = sr.get('slug')
            if not r.get('trSh'):
                r['trSh'] = k; r['trSr'] = sr.get('slug')
    rows.sort(key=lambda r: r['title'] or '')
    read  = sum(r['rdn'] for r in rows)
    watch = sum(r['wan'] for r in rows)
    out[slug] = {'name': sh.get('name_display') or sh.get('name'), 'rows': rows,
                 'read': read, 'watch': watch,
                 'nRead': sum(1 for r in rows if r['rdn']), 'nWatch': sum(1 for r in rows if r['wan'])}

dst = os.path.join(BASE, 'sheikh_stats.json')
json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('sheikhs', len(out), 'read', sum(v['read'] for v in out.values()), 'watch', sum(v['watch'] for v in out.values()))
