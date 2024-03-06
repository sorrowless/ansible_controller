#!/bin/bash
set -ux

# We control target directory carefully, so no need in 'read/while' loop here
# and overall complexity.
# shellcheck disable=SC2044
for i in $(find -E host_vars -not -path '*host_vars/.*' -type f -regex '.*(main|common).yml') ; do
# shellcheck disable=SC2016
  grep -q '$ANSIBLE_VAULT;' "$i"
  rc=$?
  if [[ $rc -ne 0 ]]; then
    hostname=$(echo "$i" | cut -d '/' -f 2)
    placement=$(grep placement "$i" | cut -d ":" -f 2 | awk '{$1=$1};1')
    host=$(grep 'ansible_host: ' "$i" | cut -d ":" -f 2)
    ip=$(grep 'ansible_ip: ' "$i" | cut -d ":" -f 2)
    if [[ -z "$ip" ]]; then
      ip=$host
    fi
    if command -v shost &> /dev/null; then
      if [[ -n "$ip" ]]; then
        if shost $ip >/dev/null; then
          additional_data="\tFound in SSH config"
        else
          additional_data="\tNot found in SSH config"
        fi
      fi
    fi
    if [[ -n "$host" ]]; then
      echo -e "$hostname\t$ip\t$host\t${placement// /-}${additional_data// /-}"
    fi
  fi
done | column -t
