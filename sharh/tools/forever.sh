#!/bin/bash
# forever.sh [PAR] — حارس الاستمرارية: يعيد run_all حتى تكتمل كل الكتب.
# شغّله مرة واحدة تحت nohup — ينجو من موت العمليات والأخطاء؛ بعد إعادة تشغيل الجهاز أعد إطلاقه بنفس الأمر.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAR="${1:-10}"
cd "$ROOT" || exit 1
while :; do
  bash tools/run_all.sh "$PAR"
  left=0
  for d in books/*/; do
    sid="$(basename "$d" | cut -d_ -f1)"
    p=$(ls "work/$sid/parts" 2>/dev/null | grep -c '\.jsonl')
    o=$(ls "work/$sid/out"   2>/dev/null | grep -c '\.jsonl')
    v=$(ls "work/$sid/verify" 2>/dev/null | grep -c '\.jsonl')
    { [ "$p" -eq 0 ] || [ "$o" -lt "$p" ] || [ "$v" -lt "$o" ]; } && left=$((left+1))
  done
  [ "$left" -eq 0 ] && break
  echo "FOREVER: $left book(s) incomplete — resuming in 60s"
  sleep 60
done
echo ALL_BOOKS_DONE
