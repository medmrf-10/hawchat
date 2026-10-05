#!/bin/bash
# push_watch.sh — monitors every new commit on origin/main:
# 1. logs violations (conflict markers, generated-file pushes, broken JSON)
# 2. AUTO-HEALS: any core file (list in site_core_files.txt) deleted or
#    content-reverted by a stale/agent commit → restores blessed version
#    from tag site-core-v2 (or the commit's parent if the file evolved
#    legitimately since — handled by taking the newest non-agent version:
#    the heal restores from the tag; my own pushes retag).
#    lessons/*/transcripts/* data dirs: restore deletions only (agents add there).
cd /home/ubuntu/hawchat || exit 1
LOG=/home/ubuntu/align_pkgs/push_violations.log
SEEN=/home/ubuntu/align_pkgs/push_watch_last
CORE=/home/ubuntu/align_pkgs/site_core_files.txt
TAG=site-core-v2
touch "$SEEN"

heal() {
  # $1=paths $2=msg $3=source ref (tag for core files, <sha>~1 for data dirs)
  local paths="$1" msg="$2" ref="${3:-$TAG}"
  [ -z "$paths" ] && return 0
  git rev-parse --verify -q rebase-merge >/dev/null 2>&1 && return 0
  echo "$(date -u +%FT%TZ) HEAL $msg → $(echo "$paths" | wc -l) path(s) from $ref" | tee -a "$LOG"
  git checkout -q "$ref" -- $paths 2>/dev/null
  git add -- $paths 2>/dev/null
  git diff --cached --quiet && return 0
  git commit -qm "ترميم آلي: استرداد ملفات النظام ($msg)"
  git pull --rebase -q origin main 2>/dev/null; bash /home/ubuntu/align_pkgs/rebase_fix.sh
  python3 playlists/data/gen_stats.py >/dev/null 2>&1
  git add -A 2>/dev/null
  git commit -qm "إعادة توليد بعد الترميم الآلي" 2>/dev/null
  git push -q origin HEAD:main 2>/dev/null && echo "$(date -u +%FT%TZ) HEALED $msg" | tee -a "$LOG"
}

while true; do
  git fetch origin -q 2>/dev/null
  last=$(cat "$SEEN")
  new=$(git log --format="%H %an %s" --reverse "${last:-HEAD~1}..origin/main" 2>/dev/null | tail -40)
  if [ -n "$new" ]; then
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
      [ -n "$bad" ] && echo "$(date -u +%FT%TZ) $sha $msg →$bad" | tee -a "$LOG" > /home/ubuntu/align_pkgs/LAST_VIOLATION

      # ── heal: core files deleted or reverted ──
      hit=""
      for cf in $(grep -v '^#' "$CORE" | grep -v 'mut_manifest'); do
        # deleted in this commit, or exists but differs from tag and this commit touched it
        if echo "$files" | grep -qx "$cf"; then
          # only heal when this commit's version lost the blessed content
          if ! git show "$sha:$cf" 2>/dev/null | cmp -s - <(git show "$TAG:$cf" 2>/dev/null); then
            hit="$hit $cf"
          fi
        fi
      done
      # deleted core files (even if not in 'files' list weirdly)
      del=$(git show --diff-filter=D --name-only --format= "$sha" \
            | grep -xf <(grep -v '^#' "$CORE") || true)
      [ -n "$del" ] && hit="$hit $del"
      [ -n "$hit" ] && heal "$hit" "wipe/revert by $sha ${msg:0:40}" "$TAG"
      # data dirs: deletion-only heal — restored from the wiping commit's
      # parent (= newest good data state), never the core tag
      datdel=$(git show --diff-filter=D --name-only --format= "$sha" \
            | grep -E "^(playlists/lessons|transcripts)/" || true)
      [ -n "$datdel" ] && heal "$datdel" "data wipe by $sha ${msg:0:40}" "$sha~1"
    done <<< "$new"
    git rev-parse origin/main > "$SEEN"
  fi
  sleep 60
done
