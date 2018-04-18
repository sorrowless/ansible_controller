#!/bin/sh

function get_roles() {
  ROLE_PATH="tools/roles_lists/$1"
  echo "Reading $ROLE_PATH list"
  if ! grep -q src $ROLE_PATH; then
    echo "Roles list $1 does not contain valid sources, skipping"
    return 0
  fi
  ansible-galaxy install -r $ROLE_PATH -p ./roles/
}

if [ -z $1 ]; then
  echo "No roles arguments was passed, checkout all roles"
  for i in `ls tools/roles_lists/` ; do
    get_roles $i
  done
else
  for i in "$@" ; do
    get_roles $i
  done
fi
exit 0
