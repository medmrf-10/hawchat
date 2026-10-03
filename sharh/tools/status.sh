#!/bin/bash
# status.sh — تقرير التقدم الموحد: أجزاء منجزة / إجمالي / معدل الساعة لكل كتاب
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
tot_p=tot_o=tot_v=0
for d in books/*/; do
  sid="$(basename "$d" | cut -d_ -f1)"
  t="$(basename "$d" | cut -d_ -f3- | cut -c1-45)"
  p=$(ls "work/$sid/parts" 2>/dev/null | grep -c '\.jsonl')
  o=$(ls "work/$sid/out"   2>/dev/null | grep -c '\.jsonl')
  v=$(ls "work/$sid/verify" 2>/dev/null | grep -c '\.jsonl')
  tot_p=$((tot_p+p)); tot_o=$((tot_o+o)); tot_v=$((tot_v+v))
  printf "%-6s %-45s parts=%-5s out=%-5s verify=%-5s\n" "$sid" "$t" "$p" "$o" "$v"
done
echo "TOTAL parts=$tot_p out=$tot_o verify=$tot_v  workers_now=$(pgrep -fc 'devin --model' 2>/dev/null || echo 0)"
