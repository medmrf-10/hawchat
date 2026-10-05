#!/usr/bin/env python3
"""Full-site consistency audit for playlists/ — FAIL on any inconsistency.
Per sheikh/row: identity key, invariants, read file exists+nonempty+count,
titles aren't filenames, no dup n, listen → series+lessons align==wan,
playlist-identity uniqueness, cov>=0.5 for aligned lessons, photos exist,
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
                # align quality: no empty align, cov>=0.5
                if r.get('wan', 0) > 0:
                    lp = os.path.join(PL, 'lessons', r['sSlug'], 'index.json')
                    li = J(lp) if os.path.exists(lp) else None
                    if li is None:
                        fails.append('%s/%s: listen but no lessons index' % (slug, rid))
                    else:
                        good = 0
                        for n in (li or {}).get('align') or []:
                            ap = os.path.join(PL, 'lessons', r['sSlug'], '%0*d.align.json' % (li.get('pad') or 3, n))
                            for cand in ('%03d.align.json' % n, '%02d.align.json' % n):
                                if not os.path.exists(ap) and os.path.exists(os.path.join(PL, 'lessons', r['sSlug'], cand)):
                                    ap = os.path.join(PL, 'lessons', r['sSlug'], cand)
                            if not os.path.exists(ap):
                                continue
                            ad = J(ap)
                            if isinstance(ad, list):
                                w, cov = ad, None
                            else:
                                w = (ad or {}).get('w') or []
                                cov = (ad or {}).get('cov')
                            if w and (cov is None or cov >= 0.5):
                                good += 1
                            elif cov is not None and cov < 0.5:
                                warns.append('%s/%s: align %s cov=%.2f<0.5' % (slug, rid, n, cov))
                        if good != r['wan']:
                            fails.append('%s/%s: good align %d vs wan %d' % (slug, rid, good, r['wan']))

for pl, rids in pl_claims.items():
    if len(set(rids)) > 1:
        fails.append('playlist %s shared by rows %s' % (pl, rids))

for w in warns: print('WARN', w)
for f in fails: print('FAIL', f)
print('audit_site: %d fails %d warns' % (len(fails), len(warns)))
sys.exit(1 if fails else 0)
