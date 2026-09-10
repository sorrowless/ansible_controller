#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

die() {
  echo "select-hosts: $*" >&2
  exit 1
}

if [[ -n "${HOST:-}" ]]; then
  printf '%s' "$HOST"
  exit 0
fi

if [[ $# -lt 1 ]]; then
  die "command argument required"
fi

if ! command -v fzf >/dev/null 2>&1; then
  die "fzf is required when HOST is not set (e.g. brew install fzf)"
fi

hosts=$($1 --list-hosts | awk '/hosts \(/{flag=1; next} /play #/{flag=0} flag && NF && $1 !~ /^pattern:/ {print $1}')

if [[ -z "$hosts" ]]; then
  die "no hosts found from '$1 --list-hosts'"
fi

selected=$(printf '%s' "$hosts" | sort -u | fzf -m \
  --prompt='Ansible host(s)> ' \
  --header='Tab: select, Enter: confirm, Esc: cancel' \
  --height=40% --reverse)

if [[ -z "$selected" ]]; then
  printf 'all'
else
  printf '%s' "$selected" | paste -sd, -
fi
