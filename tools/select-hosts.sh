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

if ! command -v fzf >/dev/null 2>&1; then
  die "fzf is required when HOST is not set (e.g. brew install fzf)"
fi

hosts=""
for dir in host_vars/*/; do
  [[ -d "$dir" ]] || continue
  name=$(basename "$dir")
  [[ "$name" == .* ]] && continue
  hosts+="${name}"$'\n'
done

if [[ -z "$hosts" ]]; then
  die "no hosts found under host_vars/"
fi

selected=$(printf '%s' "$hosts" | sort | fzf -m \
  --prompt='Ansible host(s)> ' \
  --header='Tab: select, Enter: confirm, Esc: cancel' \
  --height=40% --reverse)

if [[ -z "$selected" ]]; then
  die "no host selected"
fi

printf '%s' "$selected" | paste -sd, -
