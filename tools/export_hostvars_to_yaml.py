#!python3

from argparse import ArgumentParser
import os
import sys

import yaml


def parse_arguments():
  parser = ArgumentParser(
    description="Export Ansible host_vars main.yml files to a simple YAML list.",
  )
  parser.add_argument(
    "--host-vars-path",
    dest="host_vars_path",
    default=os.path.join(os.getcwd(), "host_vars"),
    help="Path to host_vars directory (default: ./host_vars).",
  )
  parser.add_argument(
    "--ignore-directories",
    nargs="+",
    default=[".examples"],
    help="Subdirectories in host_vars to ignore (default: .examples).",
  )

  return parser.parse_args()


def load_main_yaml(main_path: str):
  try:
    with open(main_path, "r") as fp:
      return yaml.safe_load(fp)
  except Exception:
    return None


def collect_hosts(host_vars_path: str, ignore_directories):
  result = []

  if not os.path.isdir(host_vars_path):
    print(f"host_vars path '{host_vars_path}' does not exist or is not a directory.", file=sys.stderr)
    return result

  ignore_set = set(ignore_directories)

  for host_dir_name in sorted(os.listdir(host_vars_path)):
    if host_dir_name in ignore_set:
      continue

    host_dir_path = os.path.join(host_vars_path, host_dir_name)
    if not os.path.isdir(host_dir_path):
      continue

    main_yml_path = os.path.join(host_dir_path, "main.yml")
    if not os.path.isfile(main_yml_path):
      continue

    data = load_main_yaml(main_yml_path)
    if not isinstance(data, dict):
      continue

    metainfo = data.get("metainfo") or {}
    company = metainfo.get("company")
    ansible_domainname = data.get("ansible_domainname")
    ansible_ip = data.get("ansible_ip")

    if not company or not ansible_domainname or not ansible_ip:
      # Skip hosts with incomplete data required for the export.
      continue

    result.append(
      {
        "alias": f"{company}-{ansible_domainname}".lower(),
        "hostname": ansible_ip,
        "user": "root",
        "port": 22,
      }
    )

  return result


def main():
  args = parse_arguments()
  hosts = collect_hosts(args.host_vars_path, args.ignore_directories)

  yaml.safe_dump(
    hosts,
    stream=sys.stdout,
    default_flow_style=False,
    sort_keys=False,
    allow_unicode=True,
  )


if __name__ == "__main__":
  main()

