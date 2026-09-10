#!/usr/bin/env python3

"""
Generate a combined Ansible inventory from host_vars and a static inventory.

Groups are derived from YAML filenames in host_vars/<host>/:
  host_vars/web-01/nginx.yml
  host_vars/web-01/app.yml
  host_vars/web-02/nginx.yml

produces:
  [nginx]
  web-01 
  web-02
  [app]
  web-01

The resulting inventory is merged with inventory/hosts:
  inventory/hosts + generated groups -> dynamic JSON inventory

Example:
inventory/hosts
  [all-nginx]
  web-01
  web-02

produces:
  [nginx]
  web-01 
  web-02
  [app]
  web-01
  [all-nginx]
  web-01
  web-02

Static host/group variables are preserved; hosts and groups with the same
names are merged and duplicates are removed.
"""

import json
import subprocess
import sys
from pathlib import Path


INVENTORY_DIR = Path(__file__).resolve().parent
HOST_VARS_DIR = INVENTORY_DIR / "host_vars"
STATIC_INVENTORY = INVENTORY_DIR / "hosts"


def load_static_inventory():
    """
    Load manually maintained inventory from inventory-static
    using Ansible itself.

    inventory-static can be any inventory format supported by Ansible.
    """

    if not STATIC_INVENTORY.exists():
        return {
            "_meta": {
                "hostvars": {}
            }
        }

    try:
        result = subprocess.run(
            [
                "ansible-inventory",
                "-i",
                str(STATIC_INVENTORY),
                "--list",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print(
            "ERROR: ansible-inventory not found in PATH",
            file=sys.stderr,
        )
        sys.exit(1)

    except subprocess.CalledProcessError as exc:
        print(
            "ERROR: failed to parse inventory-static:",
            file=sys.stderr,
        )
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        sys.exit(exc.returncode)

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(
            f"ERROR: invalid JSON returned by ansible-inventory: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


def build_dynamic_inventory():
    """
    Build groups based on files in host_vars.

    Example:

        host_vars/example/conf-one.yml
        host_vars/example/conf-two.yml

    becomes:

        conf-one:
          hosts:
            example:

        conf-two:
          hosts:
            example:
    """

    inventory = {
        "_meta": {
            "hostvars": {}
        }
    }

    if not HOST_VARS_DIR.exists():
        return inventory

    for host_dir in sorted(HOST_VARS_DIR.iterdir()):
        if not host_dir.is_dir():
            continue

        host = host_dir.name

        for variable_file in sorted(host_dir.iterdir()):
            if not variable_file.is_file():
                continue

            if variable_file.suffix.lower() not in {".yml", ".yaml"}:
                continue

            group = variable_file.stem

            inventory.setdefault(
                group,
                {
                    "hosts": []
                }
            )

            if host not in inventory[group]["hosts"]:
                inventory[group]["hosts"].append(host)

    return inventory


def merge_inventories(static_inventory, dynamic_inventory):
    """
    Merge static and dynamically generated inventories.

    Groups with the same name are merged.
    Hosts are deduplicated.
    Variables from static inventory are preserved.
    """

    result = {
        "_meta": {
            "hostvars": {}
        }
    }

    # Merge host variables from static inventory.
    result["_meta"]["hostvars"].update(
        static_inventory
        .get("_meta", {})
        .get("hostvars", {})
    )

    # Merge host variables from dynamic inventory.
    result["_meta"]["hostvars"].update(
        dynamic_inventory
        .get("_meta", {})
        .get("hostvars", {})
    )

    for inventory in (static_inventory, dynamic_inventory):
        for group_name, group_data in inventory.items():
            if group_name == "_meta":
                continue

            if not isinstance(group_data, dict):
                continue

            target = result.setdefault(group_name, {})

            # Hosts
            for host in group_data.get("hosts", []):
                target.setdefault("hosts", [])

                if host not in target["hosts"]:
                    target["hosts"].append(host)

            # Child groups
            for child in group_data.get("children", []):
                target.setdefault("children", [])

                if child not in target["children"]:
                    target["children"].append(child)

            # Group variables
            if "vars" in group_data:
                target.setdefault("vars", {})
                target["vars"].update(group_data["vars"])

    return result


def get_inventory():
    dynamic_inventory = build_dynamic_inventory()
    static_inventory = load_static_inventory()

    return merge_inventories(
        static_inventory,
        dynamic_inventory,
    )


def main():
    inventory = get_inventory()

    print(
        json.dumps(
            inventory,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
