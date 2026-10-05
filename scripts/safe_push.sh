#!/usr/bin/env bash
# safe_push.sh — the ONLY way fleet members should push to hawchat.
# Guarantees concurrent-push safety: always rebases on latest remote,
# then regenerates generated files deterministically before pushing.
# Usage:  bash scripts/safe_push.sh "رسالة الالتزام"   (run from repo root)
set -e
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "لست داخل مستودع hawchat"; exit 1; }
MSG="${1:-تحديث}"
# 1) stage every change the pusher made
git add -A
if git diff --cached --quiet; then echo "لا جديد للدفع."; exit 0; fi
git commit -q -m "$MSG"
# 2) rebase on remote (linear history — concurrent pushers just queue up)
for i in 1 2 3 4 5; do
  git pull --rebase -q origin main 2>/dev/null || true
  # 3) regenerate generated indexes AFTER rebase (sees everyone's files)
  [ -f playlists/series/regen_index.py ] && python3 playlists/series/regen_index.py >/dev/null 2>&1 || true
  git add playlists/series/index.json 2>/dev/null || true
  git diff --cached --quiet || git commit -q -m "rebuild index" || true
  if git push -q origin HEAD:main 2>/dev/null; then echo "دُفع بنجاح."; exit 0; fi
  sleep 2
done
echo "تعذّر الدفع بعد 5 محاولات — أعد المحاولة."; exit 1
