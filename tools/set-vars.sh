#!/bin/bash
# This small script set your env vars to automate consecutive Ansible runs.
# It sets become pass, vault file, mitogen path. Beware that it uses env vars
# and plain textfiles in /tmp/, so do not use it if you have insecure
# environment then you should not use it as env vars can be read by another
# user in some circumstances.
#
# How to use it: go to to controller repository source and run
# > . ./tools/set-vars.sh
#
# then fill asked fields and that's it.
#

# Try to determine OS
if [[ "$OSTYPE" =~ '^[D|d]arwin.*' ]]; then
  # Version of readlink which comes with MacOS doesn't support '-f' flag but
  # we're need it. So let's use GNU readlink instead
  rl="greadlink"
  # Try to determine if GNU readlink actually installed
  type $rl >/dev/null
  if [[ "$?" != "0" ]]; then
    echo "rc was $rc"
    echo 'Seems you do not have GNU readlink installed. Install it by typing "brew install coreutils"'
    return 1
  fi
else
  rl="readlink"
fi

echo -n "Become password to export: "
read -r -s ANSIBLE_BECOME_PASS
export ANSIBLE_BECOME_PASS
echo

#echo -n "Filename for vault: "
#read -r VAULT_FILENAME

echo -n "Vault password: "
read -r -s ANSIBLE_VAULT_REAL_PASS
echo
export ANSIBLE_VAULT_REAL_PASS
if [[ -n "$BASH_SOURCE" ]]; then
  SCRIPT=$($rl -f "$BASH_SOURCE")
else
  SCRIPT=$($rl -f "$0")
fi
SCRIPT_PATH=$(dirname "$SCRIPT")
VAULT_EXEC_FILE="$SCRIPT_PATH/get-vault-pass"
#echo "${ANSIBLE_VAULT_REAL_PASS}" > "/tmp/${VAULT_FILENAME}"
#export ANSIBLE_VAULT_PASSWORD_FILE=/tmp/${VAULT_FILENAME}
export ANSIBLE_VAULT_PASSWORD_FILE="$VAULT_EXEC_FILE"

echo "Check for mitogen installation"
stat library >/dev/null 2>&1
MITOGEN_PATH=$(find library -maxdepth 1 -type d -iname 'mitogen*')
if [[ -n "${MITOGEN_PATH}" ]]; then
  echo "Mitogen found in ${MITOGEN_PATH}, enable it"
  export ANSIBLE_STRATEGY_PLUGINS="${MITOGEN_PATH}/ansible_mitogen/plugins/strategy"
  export ANSIBLE_STRATEGY=mitogen_linear
  echo "Mitogen variables exported successfully"
else
  echo "Looks that Mitogen is not installed to local library, skip initialize"
fi

echo "You're all set, bye"
