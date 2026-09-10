#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

die() {
  echo "select-tags: $*" >&2
  exit 1
}

[[ -n "${TAGS:-}" ]] && { printf '%s' "$TAGS"; exit 0; }

[[ $# -lt 1 ]] && die "command argument required"
command -v fzf >/dev/null 2>&1 || die "fzf is required (brew install fzf)"

tags=$("$1" --list-tags | grep -o '\[[^]]*\]' | tr -d '[]' | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$' || true)

if [[ -z "$tags" ]]; then
  selected="all"
else
  selected=$(printf '%s' "$tags" | sort -u | fzf -m \
    --prompt='Ansible tag(s)> ' \
    --header='Tab: select, Enter: confirm, Esc: cancel' \
    --height=40% --reverse || true)
fi

if [[ -z "$selected" ]]; then
  printf 'all'
else
  printf '%s' "$selected" | paste -sd, -
fi
