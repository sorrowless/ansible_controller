#!/bin/bash

# We control target directory carefully, so no need in 'read/while' loop here
# and overall complexity.
# shellcheck disable=SC2044
for i in $(find host_vars -not -path '*host_vars/.*' -type f -iname '*.yml') ; do
# shellcheck disable=SC2016
  grep -q '$ANSIBLE_VAULT;' "$i"
  rc=$?
  if [[ $rc -ne 0 ]]; then
    hostname=$(echo $i | cut -d '/' -f 2)
    placement=$(grep placement "$i" | cut -d ":" -f 2)
    host=$(grep 'ansible_host: ' "$i" | cut -d ":" -f 2)
    ip=$(grep 'ansible_ip: ' "$i" | cut -d ":" -f 2)
    if [[ -z "$ip" ]]; then
      ip=$host
    fi
    if [[ -n "$host" ]]; then
      i=${i##*/}
      name=${i%.*}
      echo -e "$hostname\t$ip\t$host\t$name\t$placement"
    fi
  fi
done | column -t
