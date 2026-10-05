#!/bin/bash
# push_watch.sh v2 — monitors every new commit on origin/main:
# 1) logs violations (conflict markers, generated files, broken JSON)
# 2) HEALS: restores core files from site-core-v2 tag when pushed content
#    reverts/deletes them; restores data-dir deletions from the commit's parent.
# Logs to /home/ubuntu/align_pkgs/push_violations.log
cd /home/ubuntu/hawchat || exit 1
LOG=/home/ubuntu/align_pkgs/push_violations.log
SEEN=/home/ubuntu/align_pkgs/push_watch_last
CORE=/home/ubuntu/align_pkgs/site_core_files.txt
touch "$SEEN"

heal() {
  # $1 = list file of paths, $2 = message, $3 = ref to restore from
  local paths="$1" msg="$2" ref="${3:-site-core-v2}"
  [ -z "$paths" ] && return 0
  echo "$(date -u +%FT%TZ) HEAL $msg: $(echo $paths | wc -w) files" >> "$LOG"
  echo "$paths" | tr ' ' '\n' | while read -r f; do
    [ -n "$f" ] && git checkout "$ref" -- "$f" 2>/dev/null
  done
  python3 playlists/data/gen_stats.py >/dev/null 2>&1
  git add -A && git commit -qm "ترميم آلي: $msg" >/dev/null 2>&1
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
  if [ -n "$new" ]; then
    need_heal=""
    while IFS= read -r line; do
      sha=${line%% *}; msg=${line#* }
      files=$(git show --name-only --format= "$sha")
      bad=""
      for f in $files; do
        git show "$sha:$f" 2>/dev/null | grep -q "^<<<<<<<" && bad="$bad marker:$f"
      done
      echo "$files" | grep -qE "playlists/(series/index\.json|data/sheikh_stats\.json)" && bad="$bad generated"
      for f in $(echo "$files" | grep "\.json$"); do
        git show "$sha:$f" 2>/dev/null | python3 -c "import json,sys;json.load(sys.stdin)" 2>/dev/null || bad="$bad badjson:$f"
      done
      # content reverts of core files: pushed blob != site-core-v2 blob
      while read -r cf; do
        [ -z "$cf" ] || [ "${cf:0:1}" = "#" ] && continue
        if echo "$files" | grep -qx "$cf"; then
          a=$(git rev-parse -q --verify "site-core-v2:$cf" 2>/dev/null)
          b=$(git rev-parse -q --verify "$sha:$cf" 2>/dev/null)
          [ "$a" != "$b" ] && need_heal="$need_heal $cf" && bad="$bad revert:$cf"
        fi
      done < "$CORE"
      # deletions of core files or data dirs
      dels=$(git show --name-status --format= "$sha" | awk '$1=="D"{print $2}')
      for d in $dels; do
        case "$d" in
          playlists/lessons/*|lessons/*|transcripts/*) heal "$d" "استرداد محذوف $d" "$sha~1";;
          *) grep -qx "$d" "$CORE" && need_heal="$need_heal $d" && bad="$bad del:$d";;
        esac
      done
      [ -n "$bad" ] && echo "$(date -u +%FT%TZ) $sha $msg →$bad" | tee -a "$LOG" > /home/ubuntu/align_pkgs/LAST_VIOLATION
    done <<< "$new"
    # after scanning all new commits, check working tree vs tag once
    git pull --rebase -q 2>/dev/null; bash /home/ubuntu/align_pkgs/rebase_fix.sh
    still=""
    while read -r cf; do
      [ -z "$cf" ] || [ "${cf:0:1}" = "#" ] && continue
      a=$(git rev-parse -q --verify "site-core-v2:$cf" 2>/dev/null)
      [ -f "$cf" ] || { still="$still $cf"; continue; }
      b=$(git hash-object "$cf" 2>/dev/null)
      [ "$a" != "$b" ] && still="$still $cf"
    done < "$CORE"
    [ -n "$still" ] && heal "$still" "استرداد ملفات النظام المرجّعة"
    git rev-parse origin/main > "$SEEN"
  fi
  sleep 45
done
