#!/usr/bin/env bash
# safe_push.sh — the ONLY way fleet members should push to hawchat.
# Rebase on remote, regenerate ALL generated files AFTER the rebase
# (single writer: whoever pushes last owns the generated content),
# then run the audit gate before pushing.
# Usage:  bash scripts/safe_push.sh "رسالة الالتزام"   (run from repo root)
set -e
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "لست داخل مستودع hawchat"; exit 1; }
MSG="${1:-تحديث}"

git add -A
if git diff --cached --quiet; then echo "لا جديد للدفع."; exit 0; fi
git commit -q -m "$MSG"

for i in 1 2 3 4 5; do
  git pull --rebase -q origin main 2>/dev/null || true
  bash /home/ubuntu/align_pkgs/rebase_fix.sh 2>/dev/null || true
  # regenerate generated files AFTER rebase — they see everyone's files
  [ -f playlists/series/regen_index.py ] && python3 playlists/series/regen_index.py >/dev/null 2>&1 || true
  [ -f playlists/data/gen_stats.py ] && python3 playlists/data/gen_stats.py >/dev/null 2>&1 || {
    echo "تعذّر توليد الإحصائيات — تأكد من وجود playlists/data/mut_manifest.json"; }
  # stamp service-worker revision with the new commit hash → shell cache busts
  sed -i "s|^const REV = '[^']*'|const REV = 'v7-'$(git rev-parse --short HEAD)'|" sw.js 2>/dev/null || true
  git add sw.js playlists/series/index.json playlists/data/sheikh_stats.json playlists/data/read/ playlists/data/redirects.json playlists/data/search.json playlists/data/yt_titles.json 'playlists/lessons/*/index.json' 2>/dev/null || true
  git diff --cached --quiet || git commit -q -m "rebuild generated data" || true
  # audit gate: refuse to push a broken site
  if [ -f scripts/audit_site.py ]; then
    python3 scripts/audit_site.py || { echo "❌ التدقيق رفض الدفع — أصلح الأخطاء أعلاه"; exit 1; }
  fi
  if git push -q origin HEAD:main 2>/dev/null; then git tag -f site-core-v2 HEAD >/dev/null 2>&1 || true; echo "دُفع بنجاح."; exit 0; fi
  sleep 2
done
echo "تعذّر الدفع بعد 5 محاولات — أعد المحاولة."; exit 1
