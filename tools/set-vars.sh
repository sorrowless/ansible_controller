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

echo -n "Become password to export: "
read -r -s ANSIBLE_BECOME_PASS
export ANSIBLE_BECOME_PASS
echo

echo -n "Filename for vault: "
read -r VAULT_FILENAME

echo -n "Vault password: "
read -r -s ANSIBLE_VAULT_REAL_PASS
echo
echo "${ANSIBLE_VAULT_REAL_PASS}" > "/tmp/${VAULT_FILENAME}"
export ANSIBLE_VAULT_PASSWORD_FILE=/tmp/${VAULT_FILENAME}

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

