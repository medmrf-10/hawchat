#!/usr/bin/env python3
# regen_index.py — rebuild series/index.json: count + aligned per series json in this dir.
import json, glob, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
idx = json.load(open('index.json'))
by_slug = {s['slug']: s for s in idx['series']}
for f in sorted(glob.glob('*.json')):
    if f == 'index.json':
        continue
    d = json.load(open(f))
    slug = d.get('slug') or f[:-5]
    les = d.get('lessons', [])
    s = by_slug.setdefault(slug, {'slug': slug})
    s['title'] = d.get('title', s.get('title', slug))
    s['sheikh_slug'] = d.get('sheikh_slug', s.get('sheikh_slug', ''))
    s['count'] = len(les)
    # alignment + transcript truth lives in lessons/<slug>/index.json ('align'/'txt' lists of lesson numbers)
    ldir = os.path.join('..', 'lessons', slug)
    try:
        li = json.load(open(os.path.join(ldir, 'index.json')))
        s['aligned'] = len(li.get('align', []))
        s['transcribed'] = len(li.get('txt', []))
        # persist filename padding so lesson.html stops probing
        if 'pad' not in li and os.path.isdir(ldir):
            for fn in os.listdir(ldir):
                if fn.endswith(('.txt', '.align.json')):
                    stem = fn.split('.')[0]
                    if stem.isdigit():
                        li['pad'] = len(stem)
                        json.dump(li, open(os.path.join(ldir, 'index.json'), 'w'),
                                  ensure_ascii=False, indent=1)
                        break
    except Exception:
        s['aligned'] = sum(1 for l in les if l.get('align'))
        s['transcribed'] = s.get('transcribed', 0)
    if not s.get('status'):
        s['status'] = 'مكتملة التفريغ' if s['aligned'] >= s['count'] > 0 else 'مفرّغة — المحاذاة جارية'
idx['series'] = list(by_slug.values())
json.dump(idx, open('index.json', 'w'), ensure_ascii=False, indent=1)
for s in idx['series']:
    print(s['slug'], s['count'], s['aligned'])

# keep sheikh_stats.json in sync — single truth for cards + sheikh pages
import subprocess, os
try:
    subprocess.run(['python3', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'gen_stats.py')], check=False)
except Exception as e:
    print('stats regen skipped:', e)
