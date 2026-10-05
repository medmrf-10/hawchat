#!/usr/bin/env python3
# regen_index.py — rebuild series/index.json: count + aligned per series json in this dir.
# order matters: gen_stats FIRST (it rebuilds lessons/*/index.json from disk),
# then this file reads the fresh indexes — otherwise counts lag one step.
import json, glob, os, subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 1) fresh lessons indexes first — aligns/txt lists are disk-truth
try:
    subprocess.run(['python3', os.path.join('..', 'data', 'gen_stats.py')], check=False)
except Exception as e:
    print('stats regen skipped:', e)

idx = json.load(open('index.json', encoding='utf-8'))
by_slug = {s['slug']: s for s in idx['series']}
seen = set()
for f in sorted(glob.glob('*.json')):
    if f == 'index.json':
        continue
    d = json.load(open(f, encoding='utf-8'))
    slug = d.get('slug') or f[:-5]
    seen.add(slug)
    les = d.get('lessons', [])
    s = by_slug.setdefault(slug, {'slug': slug})
    s['title'] = d.get('title', s.get('title', slug))
    s['sheikh_slug'] = d.get('sheikh_slug', s.get('sheikh_slug', ''))
    s['count'] = len(les)
    # alignment + transcript truth lives in lessons/<slug>/index.json
    try:
        li = json.load(open('../lessons/%s/index.json' % slug, encoding='utf-8'))
        s['aligned'] = len(li.get('align', []))
        s['transcribed'] = len(li.get('txt', []))
    except Exception:
        s['aligned'] = sum(1 for l in les if l.get('align'))
        s['transcribed'] = s.get('transcribed', 0)
    # status always recomputed — a stale 'complete' must never survive
    if s['count'] > 0:
        s['status'] = 'مكتملة التفريغ' if s['aligned'] >= s['count'] else 'مفرّغة — المحاذاة جارية'

# drop entries whose series file is gone
for slug in list(by_slug):
    if slug not in seen:
        del by_slug[slug]

idx['series'] = list(by_slug.values())
tmp = 'index.json.tmp'
json.dump(idx, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
os.replace(tmp, 'index.json')
for s in idx['series']:
    print(s['slug'], s['count'], s['aligned'])
