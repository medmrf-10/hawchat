#!/usr/bin/env python3
"""Extract every inline <script> (no src=) from playlists/*.html and syntax-check
each with `node --check`. Catches parse-time script breakage in CI before deploy
(runtime errors are covered by smoke.py's pageerror listener)."""
import glob, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

fails = []
for path in sorted(glob.glob(os.path.join(ROOT, 'playlists', '*.html'))):
    html = open(path, encoding='utf8').read()
    for i, m in enumerate(re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S)):
        body = m.group(1)
        if not body.strip():
            continue
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf8') as f:
            f.write(body)
            tmp = f.name
        try:
            r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        finally:
            os.unlink(tmp)
        if r.returncode != 0:
            line = html[:m.start(1)].count('\n') + 1
            fails.append('%s: inline script #%d (line %d)\n%s' % (
                os.path.relpath(path, ROOT), i, line, r.stderr.strip()[:400]))

if fails:
    print('\n\n'.join(fails))
    sys.exit(1)
print('inline-js: all scripts parse')
