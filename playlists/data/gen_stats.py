#!/usr/bin/env python3
"""gen_stats.py — rebuild playlists/data/sheikh_stats.json (atomic).

Single source of truth for BOTH index cards and sheikh pages.
Per-sheikh: name, photo, order, aliases, nSeries, rows[].
Per-row: id, title, rdn, rtt, wan, wtt, read (url), listen (url or null),
rOk, wOk, kind, mutId/trSh/trSr/sSlug.

Invariants enforced: wan <= rdn <= rtt and wan <= wtt.
Also generates playlists/data/read/<rowId>.json: [{n,title,file,base}]
so tr.html can read EVERYTHING locally (no 467KB remote manifest).
"""
import json, os, re, sys, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))          # playlists/data
PL   = os.path.dirname(BASE)                                # playlists
ROOT = os.path.dirname(PL)                                  # hawchat root
MUT_TXT = 'https://medmrf-10.github.io/des/mutalaa/data/txt/'
MUT_MAN = 'https://medmrf-10.github.io/des/mutalaa/data/manifest.json'

WARN = []
def warn(m): WARN.append(m); print('WARN:', m, file=sys.stderr)

def J(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None

def norm(s):
    s = re.sub(r'[ً-ْٰ]', '', s or '')
    return re.sub(r'[^\w\s]', '', s).strip()

def fetch(u):
    try:
        return json.load(urllib.request.urlopen(u, timeout=20))
    except Exception:
        return None

# ── title cleanup ─────────────────────────────────────────────
OVR = J(os.path.join(BASE, 'title_overrides.json')) or {}
CTL = re.compile('[\\u202a-\\u202e\\u2066-\\u2069\\u00ad\\ufffd\\ufffe]')
def clean_title(t):
    t = CTL.sub('', t or '')
    t = re.sub(r'\s*English Subtitle\s*$', '', t, flags=re.I)
    t = re.sub(r'[/\\|]\s*الشيخ.*$', '', t)
    t = re.sub(r'[-–—]\s*(الشيخ|الحبيب|العلامة|الدكتور|فضيلة).*$', '', t)
    t = t.replace('_', ' ')
    t = re.sub(r'\s+', ' ', t).strip(' -–—|/\\')
    return OVR.get(t, t)

# ── lesson-list extraction from a filename list ───────────────
def rows_from_files(files, base):
    """[{n,title,file,base}] — n from NNN[_-] prefix else position."""
    out = []
    for i, f in enumerate(files or []):
        m = re.match(r'^(\d+)[_\- ]', os.path.basename(f))
        n = int(m.group(1)) if m else i + 1
        t = os.path.basename(f)
        t = re.sub(r'\.txt$', '', t)
        t = re.sub(r'^\d+[_\- ]*\d*[_\- ]*', '', t)
        t = re.split(r'[⧸｜]', t)[0]
        out.append({'n': n, 'title': clean_title(t) or f'الدرس {n}', 'file': f, 'base': base})
    return out

def rows_from_lessons(slug):
    """Read rows from playlists/lessons/<slug>/ (txt list in index.json)
    + titles from series/<slug>.json."""
    li = J(os.path.join(PL, 'lessons', slug, 'index.json')) or {}
    nums = li.get('txt') or []
    sd = J(os.path.join(PL, 'series', slug + '.json')) or {}
    titles = {l.get('n'): l.get('title') for l in sd.get('lessons', [])}
    d = os.path.join(PL, 'lessons', slug)
    out = []
    for n in nums:
        # detect file padding on disk
        fn = None
        for cand in ('%03d.txt' % n, '%02d.txt' % n, '%d.txt' % n):
            if os.path.exists(os.path.join(d, cand)):
                fn = cand; break
        if not fn:
            fn = '%03d.txt' % n
        ttl = titles.get(n) or f'الدرس {n}'
        out.append({'n': n, 'title': clean_title(re.sub(r'^.*?\|\s*', '', ttl)),
                    'file': fn, 'base': 'lessons/%s/' % slug})
    return out

# ── load sources ──────────────────────────────────────────────
sheikhs = (J(os.path.join(PL, 'data/sheikhs.json')) or {}).get('sheikhs', [])
known   = {s['slug'] for s in sheikhs}
sidx    = (J(os.path.join(PL, 'series/index.json')) or {}).get('series', [])
tr      = (J(os.path.join(ROOT, 'transcripts/index.json')) or {}).get('sheikhs', {})
man     = fetch(MUT_MAN) or {}
muts    = man if isinstance(man, list) else man.get('series', [])

order   = J(os.path.join(PL, 'shuyukh.json')) or {}
ordmap  = {}
oi = 0
for g in (order.get('groups') or []):
    for nm in (g.get('names') or []):
        oi += 1; ordmap[nm] = oi; ordmap[norm(nm)] = oi
photos = J(os.path.join(PL, 'photos.json')) or {}

for s in sidx:
    if s.get('sheikh_slug') and s['sheikh_slug'] not in known:
        warn('orphan series %s → unknown sheikh_slug %s' % (s.get('slug'), s.get('sheikh_slug')))

os.makedirs(os.path.join(BASE, 'read'), exist_ok=True)

def write_read(row_id, rows):
    p = os.path.join(BASE, 'read', row_id + '.json')
    tmp = p + '.tmp'
    json.dump(rows, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, p)

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

    def newrow(title):
        r = {'title': clean_title(title), 'rdn': 0, 'rtt': 0, 'wan': 0, 'wtt': 0,
             'kind': None}
        rows.append(r)
        return r

    # ── mutalaa manifest (readable) ──
    for m in muts:
        if not (nset & {m.get('sheikh'), norm(m.get('sheikh') or '')}):
            continue
        if (m.get('done') or 0) <= 0 and not m.get('files'):
            continue
        r = hit(m.get('name') or m.get('title') or '') or newrow(m.get('name') or m.get('title') or ('#' + str(m.get('id'))))
        n = m.get('done') or len(m.get('files') or [])
        r['rdn'] = max(r['rdn'], n)
        r['rtt'] = max(r['rtt'], m.get('total') or 0, n)
        if not r['kind']:
            r['kind'] = 'mut'; r['mutId'] = m.get('id')
        r['trSh'] = r.get('trSh'); r.setdefault('mutId', m.get('id'))
        r['_mut'] = m  # stash for read-rows

    # ── series/index.json (aligned + transcribed) ──
    for s in sidx:
        if s.get('sheikh_slug') != slug:
            continue
        if (s.get('aligned') or 0) <= 0 and (s.get('transcribed') or 0) <= 0:
            continue
        r = hit(s.get('title') or '') or newrow(s.get('title'))
        if (s.get('aligned') or 0) > 0:
            r['wan'] = max(r['wan'], s['aligned'])
            r['wtt'] = max(r['wtt'], s.get('count') or 0, s['aligned'])
            r['sSlug'] = s['slug']
        if (s.get('transcribed') or 0) > 0:
            r['rdn'] = max(r['rdn'], s['transcribed'])
            r['rtt'] = max(r['rtt'], s.get('count') or 0, s['transcribed'])
            if not r['kind']:
                r['kind'] = 's'
            r['sSlug'] = s['slug']

    # ── transcripts/index.json (push-first transcripts) ──
    for k, v in tr.items():
        if (v.get('slug') or k) != slug:
            continue
        for sr in (v.get('series') or []):
            r = hit(sr.get('title') or '') or newrow(sr.get('title'))
            n = sr.get('n') or len(sr.get('files') or [])
            r['rdn'] = max(r['rdn'], n)
            r['rtt'] = max(r['rtt'], sr.get('total') or 0, n)
            if not r['kind']:
                r['kind'] = 'tr'
            r['trSh'] = k; r['trSr'] = sr.get('slug')

    # ── enforce invariants + links + read-rows ──
    for r in rows:
        r.pop('_mut', None)
        if r['wan'] > r['rdn']:
            warn('%s/%s: wan %d > rdn %d → rdn raised' % (slug, r['title'], r['wan'], r['rdn']))
            r['rdn'] = r['wan']
        r['rtt'] = max(r['rtt'], r['rdn'])
        r['wtt'] = max(r['wtt'], r['wan'])
        if r['rtt'] and r['rdn'] > r['rtt']:
            warn('%s/%s: rdn>rtt anomaly' % (slug, r['title']))
        key = r.get('mutId') or r.get('sSlug') or ((r.get('trSh') or '') + '-' + (r.get('trSr') or ''))
        r['id'] = '%s--%s' % (slug, re.sub(r'[^\w\-]', '', str(key)))
        # read rows → data/read/<id>.json
        if r.get('kind') == 'mut' and r.get('mutId') is not None:
            m = next((x for x in muts if str(x.get('id')) == str(r['mutId'])), None)
            fl = (m or {}).get('files') or []
            write_read(r['id'], rows_from_files(fl, MUT_TXT + str(r['mutId']) + '/'))
        elif r.get('trSh') and r.get('trSr'):
            se = next((x for x in (tr[r['trSh']].get('series') or []) if x.get('slug') == r['trSr']), {})
            fl = se.get('files') or []
            write_read(r['id'], rows_from_files(fl, '../transcripts/%s/%s/' % (r['trSh'], r['trSr'])))
        elif r.get('sSlug'):
            write_read(r['id'], rows_from_lessons(r['sSlug']))
        r['read'] = 'tr.html?r=' + r['id']
        r['listen'] = ('series.html?s=' + r['sSlug']) if r['wan'] > 0 and r.get('sSlug') else None
        r['rOk'] = bool(r['rtt'] and r['rdn'] >= r['rtt'])
        r['wOk'] = bool(r['wtt'] and r['wan'] >= r['wtt'])

    rows.sort(key=lambda r: (-r['wan'], r['title'] or ''))
    read  = sum(r['rdn'] for r in rows)
    watch = sum(r['wan'] for r in rows)
    nm = sh.get('name_display') or sh.get('name') or slug
    photo = sh.get('photo') or photos.get(nm) or photos.get(sh.get('name')) or photos.get(norm(nm))
    out[slug] = {
        'name': nm,
        'photo': photo,
        'order': ordmap.get(nm) or ordmap.get(norm(nm)) or 999,
        'aliases': sh.get('aliases') or [],
        'nSeries': len(rows),
        'rows': rows,
        'read': read, 'watch': watch,
        'nRead': sum(1 for r in rows if r['rdn']),
        'nWatch': sum(1 for r in rows if r['wan']),
    }

out['_meta'] = {'updated': __import__('datetime').datetime.utcnow().isoformat() + 'Z'}
dst = os.path.join(BASE, 'sheikh_stats.json')
tmp = dst + '.tmp'
json.dump(out, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
os.replace(tmp, dst)
print('sheikhs', len(out) - 1, 'read', sum(v['read'] for k, v in out.items() if k != '_meta'),
      'watch', sum(v['watch'] for k, v in out.items() if k != '_meta'),
      'warnings', len(WARN))
