#!/usr/bin/env python3
"""gen_stats.py — rebuild playlists/data/sheikh_stats.json (atomic).

Single source of truth for BOTH index cards and sheikh pages.
Per-sheikh: name, photo, order, aliases, nSeries, rows[].
Per-row: id, title, rdn, rtt, wan, wtt, read (url), listen (url or null),
rOk, wOk, kind, mutId/trSh/trSr/sSlug/plid.

Identity: a series is its KEY (playlist id > mutId > sSlug > trSh+trSr),
never its title. Titles come literally from YouTube (yt_titles.json).
n = playlist position when the video is resolvable; rtt = playlist length.

Invariants enforced: wan <= rdn <= rtt and wan <= wtt.
wan counts only align files with non-empty w and cov>=0.5.
Also generates playlists/data/read/<rowId>.json: [{n,title,file,base}].
Manifest is pinned to data/mut_manifest.json; a fetched manifest that
shrinks >5% vs the pin is rejected (exit 2, nothing written).
"""
import json, os, re, sys, urllib.request, collections

BASE = os.path.dirname(os.path.abspath(__file__))          # playlists/data
PL   = os.path.dirname(BASE)                                # playlists
ROOT = os.path.dirname(PL)                                  # hawchat root
CAT  = '/home/ubuntu/durus/catalog/plists/'
MUT_TXT = 'https://medmrf-10.github.io/des/mutalaa/data/txt/'
MUT_MAN = 'https://medmrf-10.github.io/des/mutalaa/data/manifest.json'
MUT_PIN = os.path.join(BASE, 'mut_manifest.json')

# tr series that merge several YouTube playlists — excluded; mutalaa rows
# cover the same playlists cleanly. Files stay on disk, untouched.
TR_EXCLUDE = {('bouti', 'tawba'), ('bouti', 'rihab'), ('bouti', 'hikam'), ('bouti', 'tafsir')}
REDIRECTS = {  # old row id → new row id (best single match)
    'said-bouti--bouti-tawba': 'said-bouti--356',
    'said-bouti--bouti-rihab': 'said-bouti--337',
    'said-bouti--bouti-hikam': 'said-bouti--386',
    'said-bouti--bouti-tafsir': 'said-bouti--414',
}

WARN = []
def warn(m): WARN.append(m); print('WARN:', m, file=sys.stderr)

def J(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None

AR_DIAC = re.compile(r'[ً-ْٰ]')
def norm(s):
    s = AR_DIAC.sub('', s or '')
    s = re.sub(r'[^\w\s]', '', s)
    # fold hamza/teh-marbuta/alef-maqsura variants so names match
    s = s.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    s = s.replace('ؤ', 'و').replace('ئ', 'ي').replace('ى', 'ي').replace('ة', 'ه')
    return re.sub(r'\s+', ' ', s).strip()

def fetch(u):
    try:
        return json.load(urllib.request.urlopen(u, timeout=20))
    except Exception:
        return None

# ── title handling ────────────────────────────────────────────
OVR = J(os.path.join(BASE, 'title_overrides.json')) or {}
CTL = re.compile('[‎-‏⁦-⁩­￾]')
def yt_title(t):
    """Literal YouTube title — only control chars stripped (T221)."""
    t = CTL.sub('', t or '')
    t = re.sub(r'\s+', ' ', t).strip()
    return OVR.get(t, t)

def clean_title(t):
    t = CTL.sub('', t or '')
    t = re.sub(r'\s*English Subtitle\s*$', '', t, flags=re.I)
    t = t.replace('_', ' ')
    t = re.sub(r'\s+', ' ', t).strip(' -–—|/\\')
    return OVR.get(t, t)

# ── YouTube ground truth ──────────────────────────────────────
YTT = J(os.path.join(BASE, 'yt_titles.json')) or {}
YTV = YTT.get('v') or {}
YTP = YTT.get('p') or {}
V2P = J(os.path.join(BASE, 'vid_plists.json')) or {}   # vid → [[plid,pos,tot]]
PL_LEN = {}
def pl_len(plid):
    if plid not in PL_LEN:
        tot = None
        cp = os.path.join(CAT, plid + '.json')
        if os.path.exists(cp):
            d = J(cp) or {}
            tot = len(d.get('videos') or [])
        if tot is None:
            for v, lst in V2P.items():
                for p, pos, t in lst:
                    if p == plid:
                        tot = max(tot or 0, t)
        PL_LEN[plid] = tot
    return PL_LEN[plid]

def vid_of(fname):
    b = os.path.basename(fname)
    m = re.match(r'^NA_([\w\-]{6,})', b) or re.search(r'[\-_]([A-Za-z0-9_\-]{11})\.txt$', b)
    return m.group(1) if m else None

def series_plid(files):
    """Dominant playlist shared by these transcript files."""
    pls = collections.Counter()
    for f in files or []:
        v = vid_of(f)
        for pl, pos, tot in V2P.get(v, []) if v else []:
            pls[pl] += 1
    return pls.most_common(1)[0][0] if pls else None

def pl_pos(plid, vid):
    for p, pos, tot in V2P.get(vid, []):
        if p == plid:
            return pos
    return None

# ── lesson-list extraction ────────────────────────────────────
FILENAMEISH = re.compile(r'^[A-Za-z0-9_ \-]{3,40}$')
JUNK_FILE = re.compile(r'^(test|tmp|draft)[\W_]', re.I)

def rows_from_files(files, base, plid=None, row_title=None):
    """[{n,title,file,base}] — n = playlist position, else filename number."""
    out = []
    for i, f in enumerate(files or []):
        b = os.path.basename(f)
        if JUNK_FILE.match(b):
            continue
        v = vid_of(b)
        n = None
        if v and plid:
            n = pl_pos(plid, v)
        if n is None:
            m = re.match(r'^(\d+)[_\- ]', b)
            n = int(m.group(1)) if m else i + 1
        t = (v and YTV.get(v)) or None
        if t is None:
            t = re.sub(r'\.txt$', '', b)
            t = re.sub(r'^\d+[_\- ]*\d*[_\- ]*', '', t)
            t = clean_title(t)
        else:
            t = yt_title(t)
        # still a raw filename (no arabic)? → series title + lesson number
        if not t or (FILENAMEISH.match(t) and not re.search(r'[؀-ۿ]', t)):
            t = ((row_title or '') + ' — ' if row_title else '') + 'الدرس %d' % n
        out.append({'n': n, 'title': t, 'file': f, 'base': base})
    # never two lessons with the same n: later dups take next free number
    used = set()
    free = 1
    for r in out:
        if r['n'] in used:
            while free in used:
                free += 1
            r['n'] = free
            used.add(free)
        else:
            used.add(r['n'])
    out.sort(key=lambda r: r['n'])
    return out

def rows_from_lessons(slug):
    """Rows from playlists/lessons/<slug>/ + titles via series json."""
    li = J(os.path.join(PL, 'lessons', slug, 'index.json')) or {}
    nums = li.get('txt') or []
    d = os.path.join(PL, 'lessons', slug)
    if not nums and os.path.isdir(d):
        nums = sorted(int(m.group(1)) for fn in os.listdir(d)
                      for m in [re.match(r'^(\d+)\.txt$', fn)] if m)
    sd = J(os.path.join(PL, 'series', slug + '.json')) or {}
    titles = {l.get('n'): l.get('title') for l in sd.get('lessons', [])}
    vids = {l.get('n'): l.get('video') for l in sd.get('lessons', [])}
    pad = li.get('pad') or 3
    out = []
    for n in nums:
        fn = None
        for cand in ('%0*d.txt' % (pad, n), '%03d.txt' % n, '%02d.txt' % n, '%d.txt' % n):
            if os.path.exists(os.path.join(d, cand)):
                fn = cand; break
        if not fn:
            fn = '%0*d.txt' % (pad, n)
        v = vids.get(n)
        t = yt_title(YTV[v]) if v and v in YTV else clean_title(titles.get(n) or '')
        out.append({'n': n, 'title': t or 'الدرس %d' % n, 'file': fn, 'base': 'lessons/%s/' % slug})
    return out

def count_aligned(slug):
    """Aligned lessons that actually work: w non-empty AND cov>=0.5 (cov absent ok)."""
    d = os.path.join(PL, 'lessons', slug)
    li = J(os.path.join(d, 'index.json')) or {}
    nums = li.get('align') or []
    if not nums and os.path.isdir(d):
        nums = sorted(int(m.group(1)) for fn in os.listdir(d)
                      for m in [re.match(r'^(\d+)\.align\.json$', fn)] if m)
    pad = li.get('pad') or 3
    af = li.get('af') or {}
    good = 0
    for n in nums:
        if af.get(str(n)) or af.get(n):
            ap = os.path.join(d, af.get(str(n)) or af.get(n))
        else:
            ap = os.path.join(d, '%0*d.align.json' % (pad, n))
        if not os.path.exists(ap):
            for p2 in (3, 2, 4):
                ap = os.path.join(d, '%0*d.align.json' % (p2, n))
                if os.path.exists(ap):
                    break
            else:
                continue
        ad = J(ap)
        if not ad:
            continue
        if isinstance(ad, list):
            w, cov = ad, None
        else:
            w, cov = ad.get('w') or [], ad.get('cov')
        if w and (cov is None or cov >= 0.5):
            good += 1
    return good

def rebuild_lessons_indexes():
    """For every lessons/<slug>/ dir: merge af/tf filename maps into index.json
    (n → real filename on disk) so pages fetch exact files — no 404 probes."""
    root = os.path.join(PL, 'lessons')
    if not os.path.isdir(root):
        return
    for slug in os.listdir(root):
        d = os.path.join(root, slug)
        if not os.path.isdir(d):
            continue
        idx_path = os.path.join(d, 'index.json')
        if not os.path.exists(idx_path):
            continue
        idx = J(idx_path)
        if not isinstance(idx, dict):
            idx = {}   # corrupt/conflicted index → rebuild from disk
        af, tf = {}, {}
        for fn in os.listdir(d):
            m = re.match(r'^(\d+)\.align\.json$', fn)
            if m:
                af[int(m.group(1))] = fn
                continue
            m = re.match(r'^(\d+)\.txt$', fn)
            if m:
                tf[int(m.group(1))] = fn
        idx['af'] = af
        idx['tf'] = tf
        idx['align'] = sorted(af)   # disk is authoritative — stale lists get rebuilt
        idx['txt'] = sorted(tf)
        json.dump(idx, open(idx_path, 'w'), ensure_ascii=False, separators=(',', ':'))

# ── load sources ──────────────────────────────────────────────
rebuild_lessons_indexes()   # disk-truth first — rows count on fresh lists
sheikhs = (J(os.path.join(PL, 'data/sheikhs.json')) or {}).get('sheikhs', [])
known   = {s['slug'] for s in sheikhs}
sidx    = (J(os.path.join(PL, 'series/index.json')) or {}).get('series', [])
tr      = (J(os.path.join(ROOT, 'transcripts/index.json')) or {}).get('sheikhs', {})

# manifest: fetch fresh, else pinned; reject >5% shrink
man = fetch(MUT_MAN)
if man is None:
    man = J(MUT_PIN) or {}
    warn('manifest fetch failed → pinned copy')
else:
    _pin = J(MUT_PIN) or []
    _m = man if isinstance(man, list) else man.get('series', [])
    _p = _pin if isinstance(_pin, list) else _pin.get('series', [])
    if _p and len(_m) < len(_p) * 0.95:
        man = _pin
        warn('manifest shrank %d→%d (>5%%) → pinned copy' % (len(_p), len(_m)))
muts = man if isinstance(man, list) else man.get('series', [])

order   = J(os.path.join(PL, 'shuyukh.json')) or {}
ordmap  = {}
oi = 0
for g in (order.get('groups') or []):
    for nm in (g.get('names') or []):
        oi += 1; ordmap[nm] = oi; ordmap[norm(nm)] = oi
photos  = J(os.path.join(PL, 'photos.json')) or {}
sord    = J(os.path.join(BASE, 'series_order.json')) or {}

for s in sidx:
    if s.get('sheikh_slug') and s['sheikh_slug'] not in known:
        warn('orphan series %s → unknown sheikh_slug %s' % (s.get('slug'), s.get('sheikh_slug')))

os.makedirs(os.path.join(BASE, 'read'), exist_ok=True)

def write_read(row_id, rows):
    p = os.path.join(BASE, 'read', row_id + '.json')
    tmp = p + '.tmp'
    json.dump(rows, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, p)

def natkey(t):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', t or '')]

out = {}
for sh in sheikhs:
    slug = sh['slug']
    nset = set()
    for x in [sh.get('name_display'), sh.get('name')] + (sh.get('aliases') or []):
        if x:
            nset.add(x); nset.add(norm(x))
    rows = []

    def newrow(title):
        r = {'title': clean_title(title), 'rdn': 0, 'rtt': 0, 'wan': 0, 'wtt': 0,
             'kind': None}
        rows.append(r)
        return r

    def srow(s_slug):
        for r in rows:
            if r.get('sSlug') == s_slug:
                return r
        return None

    def trrow(k, sr_slug):
        for r in rows:
            if r.get('trSh') == k and r.get('trSr') == sr_slug:
                return r
        for r in rows:
            sl = r.get('sSlug')
            if sl and (sl == sr_slug or sl.endswith('-' + sr_slug)):
                return r
        return None

    def mutrow(m_id):
        for r in rows:
            if r.get('mutId') == m_id:
                return r
        return None

    def plrow(plid):
        for r in rows:
            if r.get('plid') == plid:
                return r
        return None

    # ── mutalaa manifest (readable) ──
    for m in muts:
        if not (nset & {m.get('sheikh'), norm(m.get('sheikh') or '')}):
            continue
        if (m.get('done') or 0) <= 0 and not m.get('files'):
            continue
        r = mutrow(m.get('id')) or newrow(m.get('name') or m.get('title') or ('#' + str(m.get('id'))))
        n = m.get('done') or len(m.get('files') or [])
        r['rdn'] = max(r['rdn'], n)
        r['rtt'] = max(r['rtt'], m.get('total') or 0, n)
        if not r['kind']:
            r['kind'] = 'mut'
        r['mutId'] = m.get('id')
        r['_mut'] = m

    # ── series/index.json (aligned + transcribed) ──
    for s in sidx:
        if s.get('sheikh_slug') != slug:
            continue
        if (s.get('aligned') or 0) <= 0 and (s.get('transcribed') or 0) <= 0:
            continue
        r = srow(s['slug']) or newrow(s.get('title'))
        _sd = J(os.path.join(PL, 'series', s['slug'] + '.json')) or {}
        _pl = (_sd.get('playlist') or '').split('list=')[-1].split('&')[0]
        if _pl:
            r['plid'] = _pl
            if YTP.get(_pl):
                r['title'] = yt_title(YTP[_pl])
            _tot = pl_len(_pl)
            if _tot:
                r['rtt'] = max(r['rtt'], _tot)
        real = count_aligned(s['slug'])
        if (s.get('aligned') or 0) > 0 or real > 0:
            r['wan'] = real
            r['wtt'] = max(r['wtt'], r['rtt'] or s.get('count') or 0, s.get('aligned') or 0, real)
            r['sSlug'] = s['slug']
        if (s.get('transcribed') or 0) > 0:
            r['rdn'] = max(r['rdn'], s['transcribed'])
            r['rtt'] = max(r['rtt'], s.get('count') or 0, s['transcribed'])
            if not r['kind']:
                r['kind'] = 's'
            r['sSlug'] = s['slug']

    # ── disk truth: lessons/<slug> + series/<slug>.json survive an index wipe ──
    lsdir = os.path.join(PL, 'lessons')
    if os.path.isdir(lsdir):
        for dsl in sorted(os.listdir(lsdir)):
            dd = os.path.join(lsdir, dsl)
            if not os.path.isdir(dd):
                continue
            real = count_aligned(dsl)
            if real <= 0 or srow(dsl):
                continue
            sd = J(os.path.join(PL, 'series', dsl + '.json')) or {}
            if sd.get('sheikh_slug') != slug:
                continue
            r = newrow(sd.get('title') or dsl)
            r['sSlug'] = dsl
            r['kind'] = r['kind'] or 's'
            r['wan'] = real
            _pl = (sd.get('playlist') or '').split('list=')[-1].split('&')[0]
            if _pl:
                r['plid'] = _pl
                if YTP.get(_pl):
                    r['title'] = yt_title(YTP[_pl])
                _tot = pl_len(_pl)
                if _tot:
                    r['rtt'] = max(r['rtt'], _tot)
            r['wtt'] = max(r['wtt'], r['rtt'] or sd.get('count') or 0, real)

    # ── transcripts/index.json (push-first transcripts) ──
    for k, v in tr.items():
        if (v.get('slug') or k) != slug:
            continue
        for sr in (v.get('series') or []):
            if (k, sr.get('slug')) in TR_EXCLUDE:
                continue
            files = sr.get('files') or []
            pl = (sr.get('playlist') or '').split('list=')[-1].split('&')[0] or series_plid(files)
            r = trrow(k, sr.get('slug')) or (plrow(pl) if pl else None) or newrow(sr.get('title'))
            # disk truth: actual txt files in transcripts dir
            dd = os.path.join(ROOT, 'transcripts', k, sr.get('slug') or '')
            disk_n = len([f for f in os.listdir(dd) if f.endswith('.txt')]) if os.path.isdir(dd) else 0
            n = max(sr.get('n') or 0, len(files), disk_n)
            r['rdn'] = max(r['rdn'], n)
            r['rtt'] = max(r['rtt'], sr.get('total') or 0, n)
            if pl:
                r['plid'] = pl
                t = pl_len(pl)
                if t:
                    r['rtt'] = max(r['rtt'], t)
                if YTP.get(pl):
                    r['title'] = yt_title(YTP[pl])
            if not r['kind']:
                r['kind'] = 'tr'
            r['trSh'] = k; r['trSr'] = sr.get('slug')

    # ── fold duplicates: same playlist = same series ──
    keep = []
    for r in rows:
        if r.get('plid'):
            tgt = next((r2 for r2 in rows if r2 is not r and r2.get('plid') == r['plid']), None)
            if tgt:
                for f_ in ('rdn', 'rtt', 'wan', 'wtt'):
                    tgt[f_] = max(tgt[f_], r[f_])
                for f_ in ('mutId', 'sSlug', 'trSh', 'trSr'):
                    if r.get(f_) and not tgt.get(f_):
                        tgt[f_] = r[f_]
                if not tgt.get('kind'):
                    tgt['kind'] = r['kind']
                continue
        # legacy title-fold for mut rows without plid
        if r.get('mutId') and not r.get('sSlug') and not r.get('plid'):
            t = norm(r['title'])
            tgt = next((r2 for r2 in rows if r2.get('sSlug') and norm(r2['title']) == t), None)
            if tgt:
                tgt['rdn'] = max(tgt['rdn'], r['rdn'])
                tgt['rtt'] = max(tgt['rtt'], r['rtt'])
                tgt['mutId'] = r['mutId']; tgt['_mut'] = r.get('_mut')
                continue
        keep.append(r)
    rows[:] = keep

    # ── invariants + links + read-rows ──
    for r in rows:
        r.pop('_mut', None)
        if r['wan'] > r['rdn']:
            r['rdn'] = r['wan']
        r['rtt'] = max(r['rtt'], r['rdn'])
        r['wtt'] = r['rtt']
        key = r.get('mutId') or r.get('sSlug') or ((r.get('trSh') or '') + '-' + (r.get('trSr') or ''))
        r['id'] = '%s--%s' % (slug, re.sub(r'[^\w\-]', '', str(key)))
        rrows = []
        if r.get('kind') == 'mut' and r.get('mutId') is not None:
            m = next((x for x in muts if str(x.get('id')) == str(r['mutId'])), None)
            fl = (m or {}).get('files') or []
            rrows = rows_from_files(fl, MUT_TXT + str(r['mutId']) + '/', r.get('plid'), r['title'])
        elif r.get('trSh') and r.get('trSr'):
            se = next((x for x in (tr[r['trSh']].get('series') or []) if x.get('slug') == r['trSr']), {})
            fl = se.get('files') or []
            if not fl:
                dd = os.path.join(ROOT, 'transcripts', r['trSh'], r['trSr'])
                if os.path.isdir(dd):
                    fl = sorted(f for f in os.listdir(dd) if f.endswith('.txt'))
            rrows = rows_from_files(fl, '../transcripts/%s/%s/' % (r['trSh'], r['trSr']), r.get('plid'), r['title'])
        elif r.get('sSlug'):
            rrows = rows_from_lessons(r['sSlug'])
        write_read(r['id'], rrows)
        if rrows and len(rrows) < r['rdn']:
            r['rdn'] = len(rrows)
        r['read'] = 'row.html?r=' + r['id']
        r['listen'] = ('row.html?r=' + r['id']) if r['wan'] > 0 and r.get('sSlug') else None
        r['rOk'] = bool(r['rtt'] and r['rdn'] >= r['rtt'])
        r['wOk'] = bool(r['rtt'] and r['wan'] >= r['rtt'])

    sordmap = sord.get(slug) or {}
    rows.sort(key=lambda r: (sordmap.get(r.get('id'), 9999), -r['wan'], natkey(r['title'])))
    read  = sum(r['rdn'] for r in rows)
    watch = sum(r['wan'] for r in rows)
    nm = sh.get('name_display') or sh.get('name') or slug
    photo = sh.get('photo') or photos.get(nm) or photos.get(sh.get('name')) or photos.get(norm(nm))
    if photo:
        photo = re.sub(r'^(\./)?playlists/', '', str(photo))
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

# degenerate-output guard: never publish stats that contradict the disk.
tot_read = sum(v['read'] for k, v in out.items() if k != '_meta')
tot_watch = sum(v['watch'] for k, v in out.items() if k != '_meta')
disk_align = 0
_ld = os.path.join(PL, 'lessons')
if os.path.isdir(_ld):
    for _s in os.listdir(_ld):
        _d = os.path.join(_ld, _s)
        if os.path.isdir(_d):
            disk_align += sum(1 for f in os.listdir(_d) if f.endswith('.align.json'))
disk_txt = 0
_td = os.path.join(ROOT, 'transcripts')
if os.path.isdir(_td):
    for _r, _, _fs in os.walk(_td):
        disk_txt += sum(1 for f in _fs if f.endswith('.txt'))
if (disk_align > 0 and tot_watch == 0) or (disk_txt > 0 and tot_read == 0):
    print('DEGENERATE OUTPUT REFUSED: disk align=%d watch=%d | disk txt=%d read=%d'
          % (disk_align, tot_watch, disk_txt, tot_read))
    print('a source index is clobbered — keeping previous sheikh_stats.json')
    import sys; sys.exit(2)

dst = os.path.join(BASE, 'sheikh_stats.json')
tmp = dst + '.tmp'
json.dump(out, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
os.replace(tmp, dst)
json.dump(REDIRECTS, open(os.path.join(BASE, 'redirects.json'), 'w'), ensure_ascii=False)
# flat search index (P7): [{id,title,sh,sname}]
search = []
for slug, v in out.items():
    if slug == '_meta':
        continue
    for r in v.get('rows') or []:
        search.append({'id': r['id'], 'title': r['title'], 'sh': slug, 'sname': v['name'],
                       'rd': r['rdn'], 'ls': r['wan']})
json.dump(search, open(os.path.join(BASE, 'search.json'), 'w'), ensure_ascii=False, separators=(',', ':'))

print('sheikhs', len(out) - 1, 'read', sum(v['read'] for k, v in out.items() if k != '_meta'),
      'watch', sum(v['watch'] for k, v in out.items() if k != '_meta'),
      'warnings', len(WARN))
