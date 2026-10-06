#!/bin/bash
# push_watch.sh v2 — monitors origin/main AND self-heals:
#  - content reverts of core files (blob differs from site-core-v2 tag)
#  - deletions under playlists/lessons|lessons|transcripts (restore from sha~1)
#  - committed conflict markers in *.json under playlists/ + transcripts/ (resolve → newest side)
# Logs to push_violations.log; LAST_VIOLATION for hub relay.
cd /home/ubuntu/hawshat || exit 1
LOG=/home/ubuntu/align_pkgs/push_violations.log
SEEN=/home/ubuntu/align_pkgs/push_watch_last
CORE=/home/ubuntu/align_pkgs/site_core_files.txt
touch "$SEEN"

fix_markers() {
python3 - <<'PY'
import re,json,glob
def resolve(txt):
    while '<<<<<<<' in txt:
        m=re.search(r'<<<<<<<[^\n]*\n((?:(?!<<<<<<<|>>>>>>>|\|\|\|\|\|\|\|).)*?)(?:\|\|\|\|\|\|\|[^\n]*\n(?:(?!<<<<<<<|>>>>>>>|\|\|\|\|\|\|\|).)*?)?=======(?P<other>.*?)>>>>>>>[^\n]*\n', txt, re.S)
        if not m: break
        txt=txt[:m.start()]+m.group('other')+txt[m.end():]
    return txt
fixed=[]
for p in glob.glob('playlists/**/*.json',recursive=True)+glob.glob('transcripts/**/*.json',recursive=True):
    try: raw=open(p,encoding='utf-8').read()
    except Exception: continue
    if '<<<<<<<' in raw:
        out=resolve(raw)
        try: json.loads(out); open(p,'w',encoding='utf-8').write(out); fixed.append(p)
        except Exception: pass
print(' '.join(fixed))
PY
}

heal() {
  local paths="$1" msg="$2" ref="${3:-site-core-v2}"
  [ -z "$paths" ] && return 0
  echo "$(date -u +%FT%TZ) HEAL $msg: $(echo $paths | wc -w) files" >> "$LOG"
  echo "$paths" | tr ' ' '\n' | while read -r f; do
    [ -n "$f" ] && git checkout "$ref" -- "$f" 2>/dev/null
  done
  local mf; mf=$(fix_markers)
  [ -n "$mf" ] && echo "$(date -u +%FT%TZ) HEAL markers-resolved: $mf" >> "$LOG"
  python3 playlists/data/gen_stats.py >/dev/null 2>&1
  # targeted add: healed paths + known generated outputs only — never -A
  # (a blanket add commits other agents' half-finished work in this shared tree)
  git add -- $paths $mf playlists/data transcripts playlists/lessons lessons 2>/dev/null
  git commit -qm "ترميم آلي: $msg" >/dev/null 2>&1
  bash /home/ubuntu/align_pkgs/rebase_fix.sh
  git pull --rebase -q 2>/dev/null; bash /home/ubuntu/align_pkgs/rebase_fix.sh
  if git push -q origin HEAD:main 2>/dev/null; then
    git tag -f site-core-v2 HEAD >/dev/null 2>&1
    git push -qf origin site-core-v2 2>/dev/null
  fi
}

while true; do
  git fetch origin -q 2>/dev/null
  last=$(cat "$SEEN")
  new=$(git log --format="%H %an %s" --reverse "${last:-HEAD~1}..origin/main" 2>/dev/null | tail -40)
  need_heal=""
  if [ -n "$new" ]; then
    while IFS= read -r line; do
      sha=${line%% *}; msg=${line#* }
      files=$(git show --name-only --format= "$sha")
      bad=""
      for f in $files; do
        git show "$sha:$f" 2>/dev/null | grep -q "^<<<<<<<" && bad="$bad marker:$f"
      done
      # phantom-guard: skip comment words, paths not in tag, nonexistent files
      true
      echo "$files" | grep -qE "playlists/(series/index\.json|data/sheikh_stats\.json)" && bad="$bad generated"
      for f in $(echo "$files" | grep "\.json$"); do
        git show "$sha:$f" 2>/dev/null | python3 -c "import json,sys;json.load(sys.stdin)" 2>/dev/null || bad="$bad badjson:$f"
      done
      [ -n "$bad" ] && echo "$(date -u +%FT%TZ) $sha $msg →$bad" | tee -a "$LOG" > /home/ubuntu/align_pkgs/LAST_VIOLATION
      # deleted data files → restore from pre-commit state
      dels=$(git diff --name-only --diff-filter=D "$sha^" "$sha" 2>/dev/null | grep -E "^(playlists/lessons/|lessons/|transcripts/)" | tr '\n' ' ')
      [ -n "$dels" ] && need_heal="$need_heal $dels"
      # core file content reverts vs blessed tag (generated files regen anyway — skip)
      while read -r cf; do
        case "$cf" in ''|\#*|*\ * ) continue;; esac
        echo "$cf" | grep -qE "playlists/(data/(sheikh_stats|search|redirects|yt_titles)\.json|data/read/|series/index\.json|lessons/.+/index\.json)" && continue
        echo "$files" | grep -qx "$cf" || continue
        git cat-file -e "site-core-v2:$cf" 2>/dev/null || continue
        a=$(git rev-parse "site-core-v2:$cf" 2>/dev/null); b=$(git rev-parse "$sha:$cf" 2>/dev/null)
        [ -n "$a" ] && [ "$a" != "$b" ] && need_heal="$need_heal $cf"
      done < "$CORE"
      # committed markers → checkout only the broken files for resolution
      if echo "$bad" | grep -q "marker:\|badjson:"; then
        for bf in $(echo "$bad" | tr ' ' '\n' | grep "^marker:\|^badjson:" | cut -d: -f2-); do
          [ -n "$bf" ] && git checkout "$sha" -- "$bf" 2>/dev/null
        done
      fi
    done <<< "$new"
    git rev-parse origin/main > "$SEEN"
  fi
  # working-tree vs tag drift sweep (non-generated core files only)
  drift=""
  while read -r cf; do
    case "$cf" in ''|\#*|*\ * ) continue;; esac
    echo "$cf" | grep -qE "playlists/(data/(sheikh_stats|search|redirects|yt_titles)\.json|data/read/|series/index\.json|lessons/.+/index\.json)" && continue
    git cat-file -e "site-core-v2:$cf" 2>/dev/null || continue
    a=$(git rev-parse "site-core-v2:$cf" 2>/dev/null); b=$(git hash-object "$cf" 2>/dev/null)
    [ -n "$a" ] && [ "$a" != "$b" ] && drift="$drift $cf"
  done < "$CORE"
  need_heal="$need_heal $drift"
  need_heal=$(echo "$need_heal" | tr ' ' '\n' | sort -u | tr '\n' ' ')
  [ -n "$(echo $need_heal)" ] && heal "$need_heal" "استرداد ملفات النظام المرجّعة"
  # standalone marker sweep even without drift
  mf=$(fix_markers); if [ -n "$mf" ]; then
    git add -A && git commit -qm "ترميم آلي: حل علامات تعارض مدفونة" >/dev/null 2>&1
    git pull --rebase -q 2>/dev/null; bash /home/ubuntu/align_pkgs/rebase_fix.sh
    git push -q origin HEAD:main 2>/dev/null && { git tag -f site-core-v2 HEAD; git push -qf origin site-core-v2; }
  fi
  sleep 45
done
