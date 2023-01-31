#!/usr/bin/env python3

import yaml
import os
import subprocess
import argparse
from git import Repo


def run_cmd(args: list) -> str:
    out = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()

    if out.returncode != 0:
        stdout_msg = stdout.decode('utf-8') if stdout is not None else ''
        stderr_msg = stderr.decode('utf-8') if stderr is not None else ''
        raise Exception(f"Command returned code {out.returncode}. Stdout: '{stdout_msg}' Stderr: '{stderr_msg}'")
    else:
      stdout_msg = stdout.decode('utf-8') if stdout is not None else ''
    return stdout_msg


def generate_run_mapping(files_mapping: dict, changed_files: list) -> dict:
  run_mapping = {}

  for file in changed_files:
    if 'host_vars' not in file and 'group_vars' not in file:
      continue
    splited_file_path = file.split("/")
    file_name = splited_file_path[-1]
    host_name = splited_file_path[-2]

    for run_file in files_mapping.get(file_name, dict()).items():
      if run_file[0] in run_mapping:
        run_mapping[run_file[0]]["limits"].append(host_name)
      else:
        run_mapping[run_file[0]] = {"limits": [host_name], "tags": run_file[1]}

  return run_mapping


def load_roles_lists() -> dict:
  roles_list = {}

  for file in os.listdir("tools/roles_lists"):
    with open("tools/roles_lists/"+file, "r") as fs:
      role_src = yaml.safe_load(fs)

    if role_src is not None:
      roles_list["tools/roles_lists/"+file] = role_src

  return roles_list


def match_role_name_src(roles_lists: dict, roles: list) -> set:
  modified_roles = set()

  for role in roles:
    for role_list in roles_lists:
      for role_src in roles_lists[role_list]:
        if role == role_src.get("name", None) or role == role_src.get("src", None):
          modified_roles.add(role_list)

  return modified_roles


def generate_roles_list(run_files: list) -> list:
  roles = []

  for run_file in run_files:
    with open(run_file, "r") as fs:
      run_file_tasks = yaml.safe_load(fs)

    for task in run_file_tasks:
      task_roles = task.get("roles", dict())
      roles.extend([ role.get("role") for role in task_roles ])

  roles_lists = load_roles_lists()
  roles = match_role_name_src(roles_lists, roles)

  return roles


def generate_ansible_commands(run_mapping: dict) -> list:
  commands = []
  for run in run_mapping.items():
    command = './{file_name} -t "{tags}" -l "{limits}"'.format(
      file_name = run[0],
      tags = ",".join(run[1]["tags"]),
      limits = ",".join(run[1]["limits"])
    )
    commands.append(command)

  return commands


def preview(target_branch: str):
  with open('tools/ci-files-mapping.yml', "r") as fs:
    files_mapping = yaml.safe_load(fs)

  changed_files = Repo().git.diff(target_branch, r=True, pretty="format:", name_only=True).split("\n")

  run_mapping = generate_run_mapping(files_mapping, changed_files)

  roles = generate_roles_list(run_mapping.keys())
  print("This roles lists will be downloaded:")
  print("\n".join(roles))

  commands = generate_ansible_commands(run_mapping)
  print("This commands will be execute:")
  print("\n".join(commands))


def apply(target_branch: str):
  with open('tools/ci-files-mapping.yml', "r") as fs:
    files_mapping = yaml.safe_load(fs)

  changed_files = Repo().git.diff(target_branch, r=True, pretty="format:", name_only=True).split("\n")

  run_mapping = generate_run_mapping(files_mapping, changed_files)

  roles = generate_roles_list(run_mapping.keys())
  for role in roles:
    run_cmd(["ansible-galaxy", "install", "-f", "-r", role, "-p", "./roles/"])
  print("This roles lists was downloaded:")
  print("\n".join(roles))

  commands = generate_ansible_commands(run_mapping)
  print("This commands will be execute:")
  print("\n".join(commands))
  for command in commands:
    run_cmd(command.split(" "))


if __name__ == '__main__':
  arg_parser = argparse.ArgumentParser()
  execution_mode = arg_parser.add_mutually_exclusive_group()

  execution_mode.add_argument("--preview",
    default=False,
    action='store_true',
    help="preview mode"
  )

  execution_mode.add_argument("--apply",
    default=False,
    action='store_true',
    help="apply mode"
  )

  arg_parser.add_argument("--target_branch",
    type=str,
    required=True,
    help="apply mode"
  )

  args = arg_parser.parse_known_args()[0]

  if args.preview:
    preview(args.target_branch)
  if args.apply:
    apply(args.target_branch)
