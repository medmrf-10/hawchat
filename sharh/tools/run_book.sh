#!/bin/bash
# run_book.sh <book_dir> <workdir> [PAR]
# Idempotent pipeline: split on toc boundaries -> parallel swe-2-max workers per part
# -> critic rounds driven by verdict (fix -> repair pass) until clean or MAX_PASSES.
# State lives in <workdir>/{parts,out,verify,logs}: re-running never repeats finished work.
BOOK="$1"; W="$2"; PAR="${3:-10}"; MAX_PASSES="${MAX_PASSES:-3}"
TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$W"/{parts,out,logs,verify}

# --- split (skips if parts already exist) ---
if [ ! -f "$W/parts/.done" ]; then
  python3 "$TOOLS/split_parts.py" "$BOOK" "$W/parts" && touch "$W/parts/.done"
fi

worker() {
  P=$1
  OUT="$W/out/$P.jsonl"
  [ -s "$OUT" ] && return 0
  sed "s|\$PART|$W/parts/$P.jsonl|g; s|\$OUT|$OUT|g" "$TOOLS/worker_prompt.md" > /tmp/wp_$$_$P.md
  for try in 1 2 3 4 5; do
    devin --model swe-2-max --permission-mode dangerous -p "$(cat /tmp/wp_$$_$P.md)" > "$W/logs/part_$P.log" 2>&1
    [ -s "$OUT" ] && return 0
    # no output = rate limit or agent error: back off and retry (rate window resets ~20min)
    grep -q "rate limit" "$W/logs/part_$P.log" && sleep $((try*90)) || sleep 30
  done
}
export -f worker 2>/dev/null; export W TOOLS

critic() {
  P=$1; R=$2
  [ -s "$W/out/$P.jsonl" ] || return 0
  VER="$W/verify/$P.r$R.jsonl"
  [ -s "$VER" ] && return 0
  sed "s|\$PART|$W/parts/$P.jsonl|g; s|\$OUT|$W/out/$P.jsonl|g; s|\$VER|$VER|g" "$TOOLS/critic_prompt.md" > /tmp/cp_$$_$P.md
  for try in 1 2 3; do
    devin --model swe-2-max --permission-mode dangerous -p "$(cat /tmp/cp_$$_$P.md)" > "$W/logs/crit_${R}_$P.log" 2>&1
    [ -s "$VER" ] && return 0
    grep -q "rate limit" "$W/logs/crit_${R}_$P.log" && sleep $((try*90)) || sleep 30
  done
}
export -f critic 2>/dev/null

parts_list() { ls "$W/parts" | grep -v '.done' | sed 's/.jsonl//'; }

# verdict fixes needed for round R: parts whose VER exists and verdict==fix
fix_list() {
  R=$1
  python3 - "$W/verify" "$R" <<'PY'
import json,sys,os
vd,r=sys.argv[1],sys.argv[2]
for f in sorted(os.listdir(vd)):
    if not f.endswith(f'.r{r}.jsonl'): continue
    try: o=json.loads(open(os.path.join(vd,f)).readline())
    except Exception: continue
    if o.get('verdict')=='fix': print(f.split('.')[0])
PY
}

# --- workers ---
parts_list | xargs -P "$PAR" -I{} bash -c 'worker {}'
echo DONE_WORKERS

# --- critic rounds with verdict-driven repair ---
R=1
while [ $R -le 2 ]; do
  parts_list | xargs -P "$PAR" -I{} bash -c 'critic {} '"$R"''
  echo DONE_CRITIC_R$R
  FIXES=$(fix_list $R)
  if [ -n "$FIXES" ] && [ $R -le $MAX_PASSES ]; then
    echo "$FIXES" | while read P; do rm -f "$W/out/$P.jsonl"; done   # force re-work
    echo "$FIXES" | xargs -P "$PAR" -I{} bash -c 'worker {}'
    echo REPAIRED_R$R
  fi
  R=$((R+1))
done
echo DONE_BOOK
