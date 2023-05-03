#!/usr/bin/env python3

from collections import defaultdict
from fnmatch import fnmatch
from glob import glob

import argparse
import os
import subprocess
import yaml
import sys

from git import Repo
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager


def run_cmd(args: list) -> str:
    '''Run given command'''
    with subprocess.Popen(args, stderr=subprocess.STDOUT) as out:
        stdout, stderr = out.communicate()

    if out.returncode != 0:
        stdout_msg = stdout.decode('utf-8') if stdout is not None else ''
        stderr_msg = stderr.decode('utf-8') if stderr is not None else ''
        # TODO(sbog): raise less broad exception
        raise Exception(
            f"Command returned code {out.returncode}. Stdout: \
            '{stdout_msg}' Stderr: '{stderr_msg}'")
    stdout_msg = stdout.decode('utf-8') if stdout is not None else ''
    return stdout_msg


def get_mapping_by_wildcard(files_mapping: dict, file: str) -> str:
    '''Get mapping by passing wildcard'''
    for file_mapping in files_mapping.get("mappings", {}).keys():
        if fnmatch(file, file_mapping):
            return file_mapping
    return ""


def generate_run_mapping(config: dict, changed_files: list, run_files: list) -> dict:
    '''Generate run mapping by given changes and run playbooks'''
    run_mapping = {}

    for file in changed_files:
        if 'host_vars' not in file and 'group_vars' not in file:
            continue
        splitted_file_path = file.split("/")
        try:
            file_name = splitted_file_path[-1]
            host_name = splitted_file_path[-2]
        # TODO(sbog): raise less broad exception
        except Exception as ex:
            print(f"Unable to find host name for file {file}")
            continue

        run_file = None
        for r_file in run_files:
            run_file = r_file if "run-" + file_name in r_file else None
            if run_file:
                break

        default_priority = config.get("default_priority")
        matched_mapping = get_mapping_by_wildcard(config, file_name)
        if matched_mapping:
            matched_mapping = config.get("mappings").get(matched_mapping)
            for mapping_run_file in matched_mapping:
                if mapping_run_file not in run_mapping:
                    run_mapping[mapping_run_file] = {"limits": set(), "tags": set(), "priority": default_priority}
                run_mapping[mapping_run_file]["limits"].add(host_name)
                run_mapping[mapping_run_file]["tags"].update(matched_mapping[mapping_run_file].get("tags", []))
                if run_mapping[mapping_run_file]["priority"] == default_priority:
                    run_mapping[mapping_run_file]["priority"] = matched_mapping[mapping_run_file].get("priority", default_priority)
                elif run_mapping[mapping_run_file]["priority"] > matched_mapping[mapping_run_file].get("priority", float('inf')):
                    run_mapping[mapping_run_file]["priority"] = matched_mapping[mapping_run_file].get("priority", default_priority)

        elif run_file is not None:
            if run_file not in run_mapping:
                run_mapping[run_file] = {"limits": set(), "tags": set(), "priority": default_priority}
            run_mapping[run_file]["limits"].add(host_name)

    return run_mapping


def difference_inventory(target_branch: str, changed_inventory: list) -> dict:
    '''Get inventory difference

       args:
           target_branch: reflog elements, like branch name of sha name

           changed_inventory: list of inventory files

       return: dict with groups as keys and hosts of these groups as values
    '''
    diff = {}
    for inventory in changed_inventory:
        new_inventory = InventoryManager(loader = DataLoader(), sources=inventory)
        new_inventory = new_inventory.get_groups_dict()

        old_file = Repo().git.show(target_branch+":"+inventory)
        with open("tmp", "w", encoding='utf-8') as f_hand:
            f_hand.write(old_file)
        old_file = InventoryManager(loader = DataLoader(), sources="tmp")
        old_file = old_file.get_groups_dict()

        for group in new_inventory:
            old_group = set(old_file.get(group, []))
            new_group = set(new_inventory.get(group, []))
            changed_hosts = list(new_group.difference(old_group))
            if changed_hosts:
                diff[group] = changed_hosts

    return diff


def get_run_files_groups(playbooks: list) -> dict:
    '''Get hosts and groups of hosts to run playbooks on

       Ansible playbooks runs on target hosts or on group of hosts which are
       defined in inventory file. This function gets list of playbooks as
       strings with filepaths, open each playbook and parse hosts/groups names
       from it.

       args:
           playbooks: list of playbooks

       return: dict with host/group as key and playbook as value
    '''
    run_groups = defaultdict(list)

    for playbook_name in playbooks:
        with open(playbook_name, "rt", encoding='utf-8') as f_hand:
            playbook_tasks = yaml.safe_load(f_hand)

        for block in playbook_tasks:
            block_hosts = block.get("hosts", None)
            if not block_hosts:
                continue
            if not isinstance(block_hosts, list):
                block_hosts = [block_hosts]
            for host in block_hosts:
                run_groups[host].append(playbook_name)

    return run_groups


def generate_run_mapping_inventory(diff_inventory: dict, playbooks: list, config: dict) -> dict:
    '''Get the data for run ansible-playbook command

       args:
           diff_inventory: dict with groups as keys and hosts of these
                                 groups as values

           playbooks: list of filepaths to playbooks

           config: configuration dict

       return: dict with playbook names as keys and limits/tags as values.
               Should be used as source for ansible-playbook command
    '''
    default_priority = config.get("default_priority")
    inventory_mapping = defaultdict(lambda: {"limits": set(), "tags": set(), "priority": default_priority})
    # Get dict with host/group as key and playbook as value
    run_groups = get_run_files_groups(playbooks)

    for group in diff_inventory:
        # There can be a case when you have changed group in inventory but
        # do not have a playbook to handle that group, we just skip them for now
        if not group in run_groups:
            continue
        # For each host in current group of changed inventory
        for host in diff_inventory[group]:
            # For each playbook which should handle current group
            for playbook in run_groups[group]:
                inventory_mapping[playbook]["limits"].add(host)

    return inventory_mapping


def generate_run_mapping_run_files(changed_files: list, config: dict) -> dict:
    '''Get the data for run ansible-playbook command

       args:
           changed_files: list of all changed files in repo

       return: dict with playbook names as keys and limits/tags as values.
               Should be used as source for ansible-playbook command
    '''
    default_priority = config.get("default_priority")
    run_files_mapping = defaultdict(lambda: {"limits": set(), "tags": set(), "priority": default_priority})

    for file in changed_files:
        if 'playbooks' not in file:
            continue

        with open(file, "rt", encoding='utf-8') as f_hand:
            playbook_tasks = yaml.safe_load(f_hand)
        
        for block in playbook_tasks: 
            run_file_hosts = block.get("hosts", None)
            if run_file_hosts:
                run_files_mapping[file]["limits"].add(run_file_hosts)
    
    return run_files_mapping


def load_roles_lists() -> dict:
    '''Get roles lists

       Open ./tools/roles_lists directory and iterate over all files in it. In
       case given file is a yaml, decide that it is a role and load it into a
       dictionary wieh filepath as key and content as value.

       args: None
       return: dictionary with filepaths and files contents
    '''
    roles_list = {}

    for file in os.listdir("tools/roles_lists"):
        with open("tools/roles_lists/"+file, "r", encoding='utf-8') as f_hand:
            role_src = yaml.safe_load(f_hand)

        if role_src is not None:
            roles_list["tools/roles_lists/"+file] = role_src

    return roles_list


def match_role_name_src(roles_lists: dict, roles: list) -> set:
    '''Returns roles set which needed to be downloaded and apply

       Gets all given roles lists which usually contain all the roles sources
       paths. Then gets all given roles which are actually the list of roles
       names to be applied. Then iterates over roles lists and for each source
       in given role list check if this source name/src matches to role names
       in roles.

       args:
           roles_lists: dict with roles lists. Looks like:
               [
                "tools/roles_lists/ldap.yml":
                  [
                    {
                     src: https://github.com/MikeCher/ansible-role-openldap.git
                     version: master
                     name: mikecher.ansible-role-openldap
                    }
                  ]
               ]

           roles: list with roles to apply. Looks like:
               [
                mikecher.ansible-role-openldap
               ]

        returns: set of roles to apply
    '''
    modified_roles = set()

    for role in roles:
        for role_list in roles_lists:
            for role_src in roles_lists[role_list]:
                if role == role_src.get("name", None) or role == role_src.get("src", None):
                    modified_roles.add(role_list)

    return modified_roles


def generate_roles_list(run_files: list) -> list:
    '''Generate roles list based on playbooks which needs to be ran

       args:
           run_files: list of playbooks which needs to be ran

       return: list of roles to download
    '''
    roles = []

    # Read all given playbooks and try to get roles names from them
    for run_file in run_files:
        with open(run_file, "r", encoding='utf-8') as f_hand:
            run_file_tasks = yaml.safe_load(f_hand)

        for task in run_file_tasks:
            task_roles = task.get("roles", {})
            for role in task_roles:
                if isinstance(role, str):
                    roles.append(role)
                else:
                    roles.append(role.get("role"))

    roles_lists = load_roles_lists()  # Just get a content of all in roles_lists directory
    # Get roles to download by ansible-galaxy
    roles = match_role_name_src(roles_lists, roles)

    return roles


def generate_ansible_commands(run_mapping: dict) -> list:
    '''Generate ansible command based on given options

       args:
           run_mapping: dict with filenames as keys and tags/limits as values

       return: list of ansible commands
    '''
    sorted_run_mapping = {}
    for run_file in run_mapping:
        priority = run_mapping[run_file].get("priority")
        if priority not in sorted_run_mapping:
            sorted_run_mapping[priority] = []
        run_mapping[run_file]["file_name"] = run_file
        sorted_run_mapping[priority].append(run_mapping[run_file])
    sorted_run_mapping = [mapping for priority in sorted(sorted_run_mapping) for mapping in sorted_run_mapping[priority]]

    commands = []
    for mapping in sorted_run_mapping:
        limits = ",".join(mapping["limits"])
        command = f'./{mapping["file_name"]} -l {limits}'

        if len(mapping["tags"]):
            tags = ",".join(mapping["tags"])
            command += f' -t {tags}'

        commands.append(command)

    return commands


def get_inventory_files(changed_files: str) -> list:
    '''Get inventory files

       Try to get inventory files from the list of overall changed_files.

       args:
         changed_files: list of str with filenames

       return: list of changed inventory files
    '''
    changed_inventory = []
    not_inventory_files = [
        "inventory/group_vars",
        "inventory/host_vars",
        "inventory/README.md"
    ]
    for file in changed_files:
        if file in not_inventory_files:
            continue
        if "inventory" in file:
            changed_inventory.append(file)
    return changed_inventory


def get_config(config_file: str = 'tools/ci-config.yml') -> dict:
    '''Get configuration from config file

       Tries to import config file and convert it into python dictionary.
       Config file should look like:

           users_vault.yml:
             playbooks/configuration/run-server-common.yml:
               - users
               - ssh_keys

       so after loading it will be a dict of dicts.

       args:
           config_file: path to the file with configuration

       return: dict with mappings
    '''
    with open(config_file, "rt", encoding='utf-8') as f_hand:
        confs = yaml.safe_load(f_hand)
    return confs


def get_playbooks(search_glob: str = "playbooks/**/*.yml") -> list:
    '''Get list of playbooks to run

       args:
           search_glob: string with directory glob to search playbooks in

       return: list of playbooks which can be ran in repository
    '''
    return list(glob(search_glob, recursive=True))


def get_changed_files(target_branch: str) -> list:
    '''Get changed files to iterate over

       Tries to get changed files in repository to run some playbooks based on
       these files info.

       args:
           target_branch: reflog element, like commit hash or branch name

       return: list of playbooks which can be ran in repository
    '''
    changed_files = Repo().git.diff(
        target_branch, r=True, pretty="format:", name_only=True) \
        .split("\n")
    changed_files = [f for f in changed_files if os.path.exists(f)]
    return changed_files


def apply(target_branch: str, dry_run: bool = False):
    '''Apply changes for given branch

       Given target branch, apply changes implemented on it.

       args:
           target_branch: reflog element, like commit hash or branch name

           dry_run: whether to really apply changes or just print what's needed
                    to be ran
    '''
    config = get_config()
    playbooks = get_playbooks()
    changed_files = get_changed_files(target_branch)
    run_mapping = generate_run_mapping(config, changed_files, playbooks)

    changed_inventory = get_inventory_files(changed_files)
    if changed_inventory:
        inventory_difference = difference_inventory(
                target_branch, changed_inventory)
        run_mapping_inventory = generate_run_mapping_inventory(
                inventory_difference, playbooks, config)
        run_mapping_inventory.update(run_mapping)
        run_mapping = run_mapping_inventory
    
    run_mapping_run_files = generate_run_mapping_run_files(changed_files, config)
    run_mapping_run_files.update(run_mapping)
    run_mapping = run_mapping_run_files

    roles = generate_roles_list(run_mapping.keys())
    print("These roles lists will be downloaded:")
    print("\n".join(roles))
    if not dry_run:
        for role in roles:
            run_cmd(["ansible-galaxy", "install", "-f", "-r", role, "-p", "./roles/"])

    commands = generate_ansible_commands(run_mapping)
    print("These commands will be executed:")
    print("\n".join(commands))
    if not dry_run:
        for command in commands:
            run_cmd(command.split(" "))


def manual_apply(playbooks: list, dry_run: bool = False):
    '''Manualy apply changes for given branch

       Given target branch, apply changes implemented on it.

       args:
           playbooks: list of bash command with playbooks to manualy run
                    format must be like follow:
                    [path_to_playbook] -l [limits] -t [tags]\n
           
           dry_run: whether to really apply changes or just print what's needed
                    to be ran
    '''

    playbooks = [playbook.strip() for playbook in playbooks.split('\n') if playbook.strip()] 
    playbooks_pathes = [playbook.split(' ')[0] for playbook in playbooks]

    roles = generate_roles_list(playbooks_pathes)
    print("These roles lists will be downloaded:")
    print("\n".join(roles))
    if not dry_run:
        for role in roles:
            run_cmd(["ansible-galaxy", "install", "-f", "-r", role, "-p", "./roles/"])

    print("These commands will be executed:")
    print("\n".join(playbooks))
    if not dry_run:
        for playbook in playbooks:
            run_cmd(playbook.split(" "))


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

    execution_mode.add_argument("--apply-manual",
      default="",
      help="manualy apply mode"
    )

    execution_mode.add_argument("--preview-manual",
      default="",
      help="manualy preview mode"
    )

    arg_parser.add_argument("--target_branch",
      type=str,
      default="",
      required='--apply' in sys.argv or '--preview' in sys.argv,
      help="apply mode"
    )

    arguments = arg_parser.parse_known_args()[0]

    if arguments.preview:
        apply(arguments.target_branch, dry_run=True)
    if arguments.apply:
        apply(arguments.target_branch)
    if arguments.preview_manual:
        manual_apply(arguments.preview_manual, dry_run=True)
    if arguments.apply_manual:
        manual_apply(arguments.apply_manual)
