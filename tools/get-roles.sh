#!/bin/bash

ROLES_PATH="tools/roles_lists"

function get_roles {
  stat "$ROLES_PATH/$1" >/dev/null 2>&1
  IS_FILENAME=$?
  if [[ "$IS_FILENAME" -ne 0 ]]; then
    echo "$1 does not look like filename, trying to find according roles"
    pushd "$ROLES_PATH" || exit 1
    for i in *.yml; do
      ROLE_NAME=$(echo "$i" | grep -i "$1")
      if [[ -n "$ROLE_NAME" ]]; then
        ROLE_PATH="$ROLES_PATH/$ROLE_NAME"
        echo "Found roles list for $1 - $ROLE_NAME, will get roles from it"
        break
      fi
    done
    popd || exit 1
  else
    ROLE_PATH="$ROLES_PATH/$1"
  fi

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
  for i in "$ROLES_PATH"/*.yml ; do
    get_roles "$i"
  done
else
  for i in "$@" ; do
    get_roles "$i"
  done
fi
exit 0

