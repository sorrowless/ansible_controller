#!/bin/bash

function get_roles {
  ROLE_PATH="tools/roles_lists/$1"
  echo "Reading $ROLE_PATH list"
  if ! grep -q src "$ROLE_PATH"; then
    echo "Roles list $1 does not contain valid sources, skipping"
    return 0
  fi
  ansible-galaxy install -r "$ROLE_PATH" -p ./roles/
}

if ! command -v ansible-galaxy ; then
  echo "Ansible-galaxy not found, cannot process..."
  exit 1
fi

if [ -z "$1" ]; then
  echo "No roles arguments was passed, checkout all roles"
  for i in tools/roles_lists/*.yml ; do
    get_roles "$i"
  done
else
  for i in "$@" ; do
    get_roles "$i"
  done
fi
exit 0

