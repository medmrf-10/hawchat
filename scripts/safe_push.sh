#!/usr/bin/env bash
# safe_push.sh v3 — fleet push protocol (single-writer):
#   agents NEVER push to main. They commit locally, then push their commit to
#   refs/inbox/<agent>-<ts>. The hub merger applies queued refs serially on a
#   clean tree, runs the gates, and is the ONLY writer to main.
# Usage:  bash scripts/safe_push.sh "رسالة الالتزام"   (run from repo root)
set -e
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "لست داخل مستودع hawchat"; exit 1; }
MSG="${1:-تحديث}"

# shared-tree wipe guard: deletions never travel through this script.
# generated files never travel either — hub rebuilds them after every merge.
git add -A
git diff --cached --diff-filter=D --name-only -z | xargs -0 -r git reset -q -- 2>/dev/null || true
git reset -q -- playlists/data/sheikh_stats.json playlists/data/search.json \
  playlists/data/redirects.json playlists/data/yt_titles.json playlists/data/read \
  playlists/series/index.json 'playlists/lessons/*/index.json' 2>/dev/null || true
if git diff --cached --quiet; then echo "لا جديد للدفع (الحذف والمولّدات لا تمر عبر safe_push)."; exit 0; fi
git commit -q -m "$MSG"

AGENT="${SAFE_PUSH_AGENT:-$(hostname -s 2>/dev/null || echo agent)}"
REF="refs/inbox/${AGENT}-$(date +%s)"
# sync base with origin/main first so the hub applies cleanly
git fetch origin -q main 2>/dev/null || true
if ! git merge-base --is-ancestor origin/main HEAD 2>/dev/null; then
  git rebase -q origin/main 2>/dev/null || { git rebase --abort 2>/dev/null;
    echo "تعارض مع main — نفّذ: git fetch origin && git reset --hard origin/main وأعد تطبيق تغييرك"; exit 1; }
fi
git push -q origin "HEAD:$REF" && echo "في الطابور: $REF — الدمج على الهب خلال دقيقة."
