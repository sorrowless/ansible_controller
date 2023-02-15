#!/usr/bin/env python3

import yaml
import os
import subprocess
import argparse
from fnmatch import fnmatch
from git import Repo
from glob import glob
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager


def run_cmd(args: list) -> str:
    out = subprocess.Popen(args, stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()

    if out.returncode != 0:
        stdout_msg = stdout.decode('utf-8') if stdout is not None else ''
        stderr_msg = stderr.decode('utf-8') if stderr is not None else ''
        raise Exception(f"Command returned code {out.returncode}. Stdout: '{stdout_msg}' Stderr: '{stderr_msg}'")
    else:
      stdout_msg = stdout.decode('utf-8') if stdout is not None else ''
    return stdout_msg


def get_mapping_by_wildcart(files_mapping: dict, file: str):
  for file_mapping in files_mapping.keys():
    if fnmatch(file, file_mapping):
      return file_mapping


def generate_run_mapping(files_mapping: dict, changed_files: list, run_files: list) -> dict:
  run_mapping = {}

  for file in changed_files:
    if 'host_vars' not in file and 'group_vars' not in file:
      continue
    splited_file_path = file.split("/")
    file_name = splited_file_path[-1]
    host_name = splited_file_path[-2]

    run_file = [file for file in run_files if "run-"+file_name in file]
    if len(run_file) > 0:
      run_file = run_file[0]
    else:
      run_file = None

    matched_mapping = get_mapping_by_wildcart(files_mapping, file_name)
    if matched_mapping is not None:
      matched_mapping = files_mapping.get(matched_mapping)
      for mapping_run_file in matched_mapping:
        if mapping_run_file not in run_mapping:
          run_mapping[mapping_run_file] = {"limits": set(), "tags": set()}
        run_mapping[mapping_run_file]["limits"].add(host_name)
        run_mapping[mapping_run_file]["tags"].update(matched_mapping[mapping_run_file])

    elif run_file is not None:
      if run_file not in run_mapping:
        run_mapping[run_file] = {"limits": set(), "tags": set()}
      run_mapping[run_file]["limits"].add(host_name)

  return run_mapping


def difference_inventory(target_branch: str, changed_inventory: list) -> dict:
  diff = {}
  for inventory in changed_inventory:
    new_inventory = InventoryManager(loader = DataLoader(), sources=inventory)
    new_inventory = new_inventory.get_groups_dict()

    old_file = Repo().git.show(target_branch+":"+inventory)
    with open("tmp", "w") as fs:
        fs.write(old_file)
    old_file = InventoryManager(loader = DataLoader(), sources="tmp")
    old_file = old_file.get_groups_dict()

    for group in new_inventory.keys():
      old_group = set(old_file.get(group, []))
      new_group = set(new_inventory.get(group, []))
      changed_hosts = list(new_group.difference(old_group))
      if len(changed_hosts) > 0:
        diff[group] = changed_hosts
  
  return diff


def get_run_files_groups(run_files: list) -> dict:
  run_groups = {}

  for run_file in run_files:
    with open(run_file, "r") as fs:
      run_file_tasks = yaml.safe_load(fs)

    for task in run_file_tasks:
      task_hosts = task.get("hosts", None)
      if task_hosts is not None:
        if isinstance(task_hosts, list):
          for task_host in task_hosts:
            if task_host not in run_groups:
              run_groups[task_host] = []
            run_groups[task_host].append(run_file) 
        else:
          if task_hosts not in run_groups:
            run_groups[task_hosts] = []
          run_groups[task_hosts].append(run_file) 

  return run_groups


def generate_run_mapping_inventory(difference_inventory: dict, run_files: list):
  inventory_mapping = {}
  run_groups = get_run_files_groups(run_files)

  for group in difference_inventory:
    if group in run_groups:
      for host in difference_inventory[group]:
        for run in run_groups[group]:
          if run not in inventory_mapping:
            inventory_mapping[run] = {"limits": set(), "tags": set()}
          inventory_mapping[run]["limits"].add(host)

  return inventory_mapping


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
      for role in task_roles:
        if isinstance(role, str):
          roles.append(role)
        else:
          roles.append(role.get("role"))

  roles_lists = load_roles_lists()
  roles = match_role_name_src(roles_lists, roles)

  return roles


def generate_ansible_commands(run_mapping: dict) -> list:
  commands = []
  for run in run_mapping.items():
    command = './{file_name} -l {limits}'.format(
      file_name = run[0],
      limits = ",".join(run[1]["limits"])
    )

    if len(run[1]["tags"]) != 0:
      command += ' -t {tags}'.format(
        tags = ",".join(run[1]["tags"])
      )

    commands.append(command)

  return commands


def preview(target_branch: str):
  with open('tools/ci-files-mapping.yml', "r") as fs:
    files_mapping = yaml.safe_load(fs)
  run_files = [file for file in glob("playbooks/**/*.yml", recursive=True)]
  changed_files = Repo().git.diff(target_branch, r=True, pretty="format:", name_only=True).split("\n")
  run_mapping = generate_run_mapping(files_mapping, changed_files, run_files)

  not_inventory_files = ["inventory/group_vars", "inventory/host_vars", "inventory/README.md"]
  changed_inventory = [file for file in changed_files if "inventory" in file and file not in not_inventory_files]
  if len(changed_inventory) > 0:
    run_mapping = {**run_mapping, **generate_run_mapping_inventory(difference_inventory(target_branch, changed_inventory), run_files)}

  roles = generate_roles_list(run_mapping.keys())
  print("This roles lists will be downloaded:")
  print("\n".join(roles))

  commands = generate_ansible_commands(run_mapping)
  print("This commands will be execute:")
  print("\n".join(commands))


def apply(target_branch: str):
  with open('tools/ci-files-mapping.yml', "r") as fs:
    files_mapping = yaml.safe_load(fs)
  run_files = [file for file in glob("playbooks/**/*.yml", recursive=True)]
  changed_files = Repo().git.diff(target_branch, r=True, pretty="format:", name_only=True).split("\n")
  run_mapping = generate_run_mapping(files_mapping, changed_files, run_files)

  not_inventory_files = ["inventory/group_vars", "inventory/host_vars", "inventory/README.md"]
  changed_inventory = [file for file in changed_files if "inventory" in file and file not in not_inventory_files]
  if len(changed_inventory) > 0:
    run_mapping = {**run_mapping, **generate_run_mapping_inventory(difference_inventory(target_branch, changed_inventory), run_files)}

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
