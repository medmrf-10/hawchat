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
    s['aligned'] = sum(1 for l in les if l.get('align'))
    if not s.get('status'):
        s['status'] = 'مكتملة التفريغ' if s['aligned'] >= s['count'] > 0 else 'مفرّغة — المحاذاة جارية'
idx['series'] = list(by_slug.values())
json.dump(idx, open('index.json', 'w'), ensure_ascii=False, indent=1)
for s in idx['series']:
    print(s['slug'], s['count'], s['aligned'])
