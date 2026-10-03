#!/bin/bash
# run_all.sh [PAR] — يشغّل كل كتب الحزمة بالتتابع من جذر الحزمة المفكوكة.
# آمن للإعادة بعد أي انقطاع: الأجزاء المنجزة تُتخطى تلقائياً، والعمل يكمل من حيث توقف.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAR="${1:-10}"
cd "$ROOT" || exit 1
for d in books/*/; do
  sid="$(basename "$d" | cut -d_ -f1)"
  p=$(ls "work/$sid/parts" 2>/dev/null | grep -c '\.jsonl')
  o=$(ls "work/$sid/out"   2>/dev/null | grep -c '\.jsonl')
  v=$(ls "work/$sid/verify" 2>/dev/null | grep -c '\.jsonl')
  # complete = every part has out AND at least one verify round on every out
  if [ "$p" -gt 0 ] && [ "$o" -ge "$p" ] && [ "$v" -ge "$o" ]; then
    echo "SKIP $sid (done $o/$p)"; continue
  fi
  echo "BOOK $sid (parts=$p out=$o)"
  bash tools/run_book.sh "$d" "work/$sid" "$PAR"
done
echo RUN_ALL_DONE
