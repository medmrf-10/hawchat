#!/bin/bash
# push_done.sh <agent_name> [repo_dir] — يرفع out+verify لكل كتبك المنجزة إلى sharh/inbox/<agent>/ في الريبو.
# آمن للتكرار: يدفع فقط ما جدّ. شغّله دورياً (أو بعد كل كتاب) كي لا تضيع النتائج مع جهازك.
AGENT="$1"; REPO="${2:-$HOME/hawchat}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -z "$AGENT" ] && { echo "usage: push_done.sh <agent> [repo]"; exit 1; }
cd "$REPO" && git pull --rebase --autostash -q || true
mkdir -p "sharh/inbox/$AGENT"
for d in "$ROOT"/work/*/; do
  sid="$(basename "$d")"
  mkdir -p "sharh/inbox/$AGENT/out/$sid" "sharh/inbox/$AGENT/verify/$sid"
  cp -n "$d"out/*.jsonl "sharh/inbox/$AGENT/out/$sid/" 2>/dev/null
  cp -n "$d"verify/*.jsonl "sharh/inbox/$AGENT/verify/$sid/" 2>/dev/null
done
cd "$REPO"
git add "sharh/inbox/$AGENT" || exit 0
git diff --cached --quiet && { echo "nothing new"; exit 0; }
git commit -q -m "sharh inbox $AGENT: $(date -u +%H:%M)" && git push -q origin main && echo PUSHED
