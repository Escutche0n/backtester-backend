#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: ./scripts/backup_git.sh \"commit message\""
  exit 1
fi

message="$1"

git add .

if git diff --cached --quiet; then
  echo "nothing to commit"
  exit 0
fi

git commit -m "$message"
git push
