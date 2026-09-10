#!/usr/bin/env python3
"""
Generate an SSH config block from Ansible host_vars/<host>/main.yml.

For each host, ansible_host/ansible_ip, ansible_port, ansible_user and
ansible_ssh_common_args are converted to an OpenSSH Host block.

Example:

    host_vars/web-01/main.yml:
        ansible_host: 10.0.0.11
        ansible_port: 22

    host_vars/web-02/main.yml:
        ansible_host: 10.0.0.12
        ansible_user: admin

produces:

    Host web-01
        HostName 10.0.0.11
        Port 22

    Host web-02
        HostName 10.0.0.12
        Port 22
        User admin

The generated blocks are wrapped in #ac_start/#ac_end markers and inserted
or replaced only for the current controller in ~/.ssh/config. Existing
content outside the block is preserved.
"""

import argparse
import os
import re
import sys
from pathlib import Path

import yaml


BLOCK_START = "#ac_start {name}"
BLOCK_END = "#ac_end {name}"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export Ansible host_vars to SSH config"
    )

    parser.add_argument(
        "--prefix",
        default="",
        help="Prefix for SSH Host names, e.g. infra-",
    )

    parser.add_argument(
        "--user",
        default=None,
        help=(
            "Override SSH user. If not specified, ANSIBLE_USER "
            "environment variable is used when available."
        ),
    )

    parser.add_argument(
        "--ac-name",
        default=None,
        help=(
            "Controller name used for ac_start/ac_end markers. "
            "Defaults to controller directory name."
        ),
    )

    parser.add_argument(
        "--ssh-conf",
        default="~/.ssh/config",
        help=(
            "Path to SSH config file. "
            "Defaults to ~/.ssh/config"
        ),
    )

    return parser.parse_args()


def find_controller_root():
    """
    Script is expected to be located in:

        controller/tools/export_ssh_config.py

    Controller root is therefore the parent directory of tools.
    """
    script_dir = Path(__file__).resolve().parent
    controller_root = script_dir.parent

    return controller_root


def load_hosts(controller_root):
    """
    Read:

        host_vars/<host>/main.yml

    main.yml is actually YAML despite the .py extension.
    """

    host_vars_dir = controller_root / "host_vars"

    if not host_vars_dir.is_dir():
        raise RuntimeError(
            f"host_vars directory not found: {host_vars_dir}"
        )

    hosts = []

    for host_dir in sorted(host_vars_dir.iterdir()):
        if not host_dir.is_dir():
            continue

        main_file = host_dir / "main.yml"

        if not main_file.is_file():
            print(
                f"WARNING: {main_file} not found, skipping {host_dir.name}",
                file=sys.stderr,
            )
            continue

        try:
            with main_file.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        except yaml.YAMLError as exc:
            raise RuntimeError(
                f"Failed to parse {main_file}: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                f"{main_file} must contain a YAML mapping"
            )

        hosts.append(
            {
                "name": host_dir.name,
                "data": data,
            }
        )

    return hosts


def get_user(args):
    """
    Priority:

    1. --user
    2. ANSIBLE_USER environment variable
    3. ansible_user from main.yml, if it is a literal value
    4. no User directive
    """

    if args.user:
        return args.user

    env_user = os.environ.get("ANSIBLE_USER")
    if env_user:
        return env_user

    return None


def normalize_proxy_command(proxy_command):
    """
    Convert Ansible's ansible_ssh_common_args:

        -o ProxyCommand='ssh -W %h:%p -q {{ ansible_user }}@158.160.4.141'

    into something suitable for ~/.ssh/config.

    The SSH config itself doesn't understand Jinja, so
    {{ ansible_user }} is replaced with the actual user when possible.
    """

    if not proxy_command:
        return None

    proxy_command = str(proxy_command).strip()

    # Remove surrounding quotes if the whole value was quoted.
    if (
        len(proxy_command) >= 2
        and proxy_command[0] == proxy_command[-1]
        and proxy_command[0] in {"'", '"'}
    ):
        proxy_command = proxy_command[1:-1]

    return proxy_command


def render_host(host, prefix, user):
    """
    Render one SSH Host block.
    """

    name = host["name"]
    data = host["data"]

    ansible_host = data.get("ansible_host") or data.get("ansible_ip")

    if not ansible_host:
        raise RuntimeError(
            f"Host {name}: ansible_host/ansible_ip is missing"
        )

    ansible_port = data.get("ansible_port", 22)

    lines = [
        f"Host {prefix}{name}",
        f"    HostName {ansible_host}",
        f"    Port {ansible_port}",
    ]

    if user:
        lines.append(f"    User {user}")
    else:
        # If ansible_user is a literal value, use it.
        ansible_user = data.get("ansible_user")

        if (
            isinstance(ansible_user, str)
            and "{{" not in ansible_user
            and "lookup(" not in ansible_user
        ):
            lines.append(f"    User {ansible_user}")

    proxy_command = normalize_proxy_command(
        data.get("ansible_ssh_common_args")
    )

    if proxy_command:
        # Replace Jinja expression if it somehow exists.
        if user:
            proxy_command = proxy_command.replace(
                "{{ ansible_user }}",
                user,
            )

        # ansible_ssh_common_args normally contains:
        #
        # -o ProxyCommand='ssh ...'
        #
        # OpenSSH config needs:
        #
        # ProxyCommand ssh ...
        #
        match = re.search(
            r"-o\s+ProxyCommand=(['\"]?)(.*?)\1$",
            proxy_command,
        )

        if match:
            command = match.group(2)

            if user:
                command = command.replace(
                    "{{ ansible_user }}",
                    user,
                )

            lines.append(f"    ProxyCommand {command}")
        else:
            # Keep unknown SSH common args as-is rather than silently
            # dropping them.
            lines.append(f"    # ansible_ssh_common_args: {proxy_command}")

    return "\n".join(lines)


def render_block(controller_name, hosts, prefix, user):
    """
    Render complete controller block.
    """

    start = BLOCK_START.format(name=controller_name)
    end = BLOCK_END.format(name=controller_name)

    lines = [
        start,
        "",
    ]

    for index, host in enumerate(hosts):
        lines.append(
            render_host(
                host,
                prefix,
                user,
            )
        )

        if index != len(hosts) - 1:
            lines.append("")

    lines.extend(
        [
            "",
            end,
        ]
    )

    return "\n".join(lines)


def replace_or_append_block(content, controller_name, new_block):
    """
    Replace only:

        #ac_start <controller_name>
        ...
        #ac_end <controller_name>

    Everything outside this block remains unchanged.
    """

    start_marker = re.escape(
        BLOCK_START.format(name=controller_name)
    )
    end_marker = re.escape(
        BLOCK_END.format(name=controller_name)
    )

    pattern = re.compile(
        rf"(?ms)^"
        rf"{start_marker}"
        rf"\s*$"
        rf".*?"
        rf"^"
        rf"{end_marker}"
        rf"\s*$"
    )

    matches = list(pattern.finditer(content))

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple SSH config blocks found for controller "
            f"{controller_name!r}"
        )

    if len(matches) == 1:
        match = matches[0]

        before = content[:match.start()]
        after = content[match.end():]

        return (
            before.rstrip("\n")
            + "\n\n"
            + new_block
            + "\n"
            + after.lstrip("\n")
        )

    # Block doesn't exist yet.
    if content.strip():
        return (
            content.rstrip("\n")
            + "\n\n"
            + new_block
            + "\n"
        )

    return new_block + "\n"


def main():
    args = parse_args()

    controller_root = find_controller_root()

    controller_name = (
        args.ac_name
        if args.ac_name
        else controller_root.name
    )

    ssh_conf = (
        Path(args.ssh_conf).expanduser()
        if args.ssh_conf
        else controller_root.parent / "ssh" / "conf"
    )

    user = get_user(args)

    print(f"Controller: {controller_root}")
    print(f"AC name:    {controller_name}")
    print(f"SSH config: {ssh_conf}")
    print(f"Prefix:     {args.prefix}")
    print(f"User:       {user or '(not specified)'}")

    hosts = load_hosts(controller_root)

    print(f"Hosts:      {len(hosts)}")

    new_block = render_block(
        controller_name=controller_name,
        hosts=hosts,
        prefix=args.prefix,
        user=user,
    )

    if ssh_conf.exists():
        content = ssh_conf.read_text(encoding="utf-8")
    else:
        content = ""

    new_content = replace_or_append_block(
        content=content,
        controller_name=controller_name,
        new_block=new_block,
    )

    if new_content == content:
        print("SSH config is already up to date.")
        return

    ssh_conf.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ssh_conf.write_text(
        new_content,
        encoding="utf-8",
    )

    print(f"Updated: {ssh_conf}")


if __name__ == "__main__":
    main()
