#!/usr/bin/env python3
"""Full-site consistency audit for playlists/ — FAIL on any inconsistency.
Per sheikh/row: identity key, invariants, read file exists+nonempty+count,
titles aren't filenames, no dup n, listen → series+lessons align==wan,
playlist-identity uniqueness, cov>=0.3 for aligned lessons, photos exist,
no order==999 sheikhs. Usage: python3 scripts/audit_site.py [root]"""
import json, os, re, sys, collections

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..')
PL = os.path.join(ROOT, 'playlists')
fails, warns = [], []

def J(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception as e:
        fails.append('invalid json %s: %s' % (p, e)); return None

FILENAME_TITLE = re.compile(r'^(NA )?[A-Za-z0-9_\- ]{8,20}$|AlAmri|AbdelMonem|^\d{3}_|test write', re.I)

st = J(os.path.join(PL, 'data/sheikh_stats.json')) or {}
pl_claims = collections.defaultdict(list)   # playlistId -> [rowId]
seen_ids = set()

for slug, s in st.items():
    if slug == '_meta' or not isinstance(s, dict):
        continue
    if s.get('order') == 999 and (s.get('read', 0) + s.get('watch', 0)) > 0:
        warns.append('%s: order=999 despite content' % slug)
    rows = s.get('rows') or []
    if s.get('read', 0) + s.get('watch', 0) > 0 and not rows:
        fails.append('%s: counters>0 but no rows' % slug)
    # photo exists?
    ph = s.get('photo')
    if ph and not os.path.exists(os.path.join(PL, ph)):
        fails.append('%s: photo missing %s' % (slug, ph))

    for r in rows:
        rid = r.get('id')
        if not rid:
            fails.append('%s: row without id %r' % (slug, r.get('title'))); continue
        if rid in seen_ids:
            fails.append('%s/%s: duplicate row id' % (slug, rid))
        seen_ids.add(rid)
        if not (r.get('mutId') or r.get('sSlug') or r.get('trSh')):
            fails.append('%s/%s: no identity key' % (slug, rid))
        if not (0 <= r.get('wan', 0) <= r.get('rdn', 0) <= r.get('rtt', 0)):
            fails.append('%s/%s: invariant wan<=rdn<=rtt broken (%s/%s/%s)' % (slug, rid, r['wan'], r['rdn'], r['rtt']))
        if r.get('read') and not r['read'].startswith('row.html?r='):
            fails.append('%s/%s: read link not row.html' % (slug, rid))
        if r.get('listen') and r.get('wan', 0) <= 0:
            fails.append('%s/%s: listen link with wan=0' % (slug, rid))
        if r.get('wan', 0) > 0 and not r.get('listen'):
            fails.append('%s/%s: wan>0 but no listen link' % (slug, rid))

        # read file: exists, count==rdn, no dup n, real titles
        rp = os.path.join(PL, 'data/read', rid + '.json')
        if not os.path.exists(rp):
            fails.append('%s/%s: missing read file' % (slug, rid))
        else:
            rd = J(rp)
            if rd is not None:
                if not rd and r.get('rdn', 0) > 0:
                    fails.append('%s/%s: read file empty but rdn=%d' % (slug, rid, r['rdn']))
                elif rd and len(rd) != r.get('rdn', 0):
                    fails.append('%s/%s: read file %d rows vs rdn %d' % (slug, rid, len(rd), r['rdn']))
                ns = [x.get('n') for x in rd]
                dup_n = [n for n, c in collections.Counter(ns).items() if c > 1]
                if dup_n:
                    fails.append('%s/%s: duplicate n %s' % (slug, rid, dup_n[:6]))
                ft = [x['title'][:30] for x in rd if FILENAME_TITLE.match((x.get('title') or '').strip())]
                if ft:
                    fails.append('%s/%s: %d filename-titles e.g. %r' % (slug, rid, len(ft), ft[:3]))
                tc = collections.Counter((x.get('title') or '').strip() for x in rd)
                if rd and max(tc.values()) > max(5, int(len(rd) * .5)):
                    warns.append('%s/%s: %d%% lessons share one title' % (slug, rid, int(100 * max(tc.values()) / len(rd))))

        # series identity: playlist uniqueness
        if r.get('sSlug'):
            sp = os.path.join(PL, 'series', r['sSlug'] + '.json')
            if not os.path.exists(sp):
                fails.append('%s/%s: missing series/%s.json' % (slug, rid, r['sSlug']))
            else:
                sd = J(sp) or {}
                pl = (sd.get('playlist') or '').split('list=')[-1].split('&')[0]
                if pl:
                    pl_claims[pl].append(rid)
                elif r.get('wan', 0) > 0:
                    warns.append('%s/%s: series with align but no playlist link' % (slug, rid))
                # align + text integrity (F7/A10): af/tf are the authoritative
                # n→filename maps written by the builder — audit what the pages
                # actually resolve, never pad-guess filenames.
                lp = os.path.join(PL, 'lessons', r['sSlug'], 'index.json')
                li = J(lp) if os.path.exists(lp) else None
                if r.get('wan', 0) > 0 and li is None:
                    fails.append('%s/%s: listen but no lessons index' % (slug, rid))
                if li is not None:
                    ldir = os.path.join(PL, 'lessons', r['sSlug'])
                    af = li.get('af') or {}
                    tf = li.get('tf') or {}
                    align_ok = set(li.get('alignOk') or [])
                    for n, fn in list(af.items()) + list(tf.items()):
                        if not os.path.exists(os.path.join(ldir, fn)):
                            fails.append('%s/%s: index lists %s but file missing' % (slug, rid, fn))
                    # A10: every alignOk lesson's text must resolve the same way
                    # tr.html resolves it — tf name → read row same n → probe
                    # 3- then 2-digit pad. No resolution = the reader 404s.
                    read_ns = set()
                    rp2 = os.path.join(PL, 'data/read', rid + '.json')
                    if os.path.exists(rp2):
                        rd2 = J(rp2)
                        if isinstance(rd2, list):
                            read_ns = {x.get('n') for x in rd2}
                    def text_resolves(n):
                        if str(n) in tf:
                            return True
                        if n in read_ns:
                            return True
                        for cand in ('%03d.txt' % n, '%02d.txt' % n):
                            if os.path.exists(os.path.join(ldir, cand)):
                                return True
                        return False
                    for n in align_ok:
                        if not text_resolves(n):
                            fails.append('%s/%s: alignOk lesson %s has no resolvable text' % (slug, rid, n))
                    good = 0
                    for nk, fn in af.items():
                        ap = os.path.join(ldir, fn)
                        if not os.path.exists(ap):
                            continue
                        ad = J(ap)
                        if isinstance(ad, list):
                            w, cov = ad, None
                        else:
                            w = (ad or {}).get('w') or []
                            cov = (ad or {}).get('cov')
                        if w and (cov is None or cov >= 0.3):
                            good += 1
                        elif cov is not None and cov < 0.3 and w:
                            warns.append('%s/%s: align %s cov=%.2f<0.3 with %d words' % (slug, rid, nk, cov, len(w)))
                    if r.get('wan', 0) > 0:
                        if good != r['wan']:
                            fails.append('%s/%s: good align %d vs wan %d' % (slug, rid, good, r['wan']))
                        if len(align_ok) != r['wan']:
                            fails.append('%s/%s: alignOk %d vs wan %d' % (slug, rid, len(align_ok), r['wan']))
                    # series lessons hygiene: dur mm:ss, Arabic title, textless count
                    textless = 0
                    for l in (sd.get('lessons') or []):
                        d = l.get('dur')
                        if d is not None and not re.match(r'^\d+:\d{2}$', str(d)):
                            warns.append('%s/%s: lesson %s bad dur %r' % (slug, rid, l.get('n'), d))
                        t = (l.get('title') or '').strip()
                        if t and not re.search(r'[؀-ۿ]', t):
                            warns.append('%s/%s: lesson %s non-Arabic title %r' % (slug, rid, l.get('n'), t[:40]))
                        if l.get('video') and not text_resolves(l.get('n')):
                            textless += 1
                    if textless:
                        warns.append('%s/%s: %d series lessons with no text' % (slug, rid, textless))

for pl, rids in pl_claims.items():
    if len(set(rids)) > 1:
        fails.append('playlist %s shared by rows %s' % (pl, rids))

for w in warns: print('WARN', w)
for f in fails: print('FAIL', f)
print('audit_site: %d fails %d warns' % (len(fails), len(warns)))
sys.exit(1 if fails else 0)
