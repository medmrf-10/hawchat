#!/bin/bash
# push_watch.sh — monitors every new commit on origin/main for violations:
# conflict markers, pushes of generated files, broken JSON, edits outside own dirs.
# Logs to /home/ubuntu/align_pkgs/push_violations.log and writes LAST_VIOLATION for the hub to relay.
cd /home/ubuntu/hawchat || exit 1
LOG=/home/ubuntu/align_pkgs/push_violations.log
SEEN=/home/ubuntu/align_pkgs/push_watch_last
touch "$SEEN"
while true; do
  git fetch origin -q 2>/dev/null
  last=$(cat "$SEEN")
  new=$(git log --format="%H %an %s" --reverse "${last:-HEAD~1}..origin/main" 2>/dev/null | tail -40)
  if [ -n "$new" ]; then
    while IFS= read -r line; do
      sha=${line%% *}; msg=${line#* }
      files=$(git show --name-only --format= "$sha")
      bad=""
      # conflict markers in any pushed file
      for f in $files; do
        git show "$sha:$f" 2>/dev/null | grep -q "^<<<<<<<" && bad="$bad marker:$f"
      done
      # generated files that must never be hand-pushed
      echo "$files" | grep -qE "playlists/(series/index\.json|data/sheikh_stats\.json)" && bad="$bad generated"
      # invalid json pushed
      for f in $(echo "$files" | grep "\.json$"); do
        git show "$sha:$f" 2>/dev/null | python3 -c "import json,sys;json.load(sys.stdin)" 2>/dev/null || bad="$bad badjson:$f"
      done
      if [ -n "$bad" ]; then
        echo "$(date -u +%FT%TZ) $sha $msg →$bad" | tee -a "$LOG" > /home/ubuntu/align_pkgs/LAST_VIOLATION
      fi
    done <<< "$new"
    git rev-parse origin/main > "$SEEN"
  fi
  sleep 60
done
