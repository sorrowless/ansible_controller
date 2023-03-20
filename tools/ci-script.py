#!/usr/bin/env python3

from collections import defaultdict
from fnmatch import fnmatch
from glob import glob

import argparse
import os
import subprocess
import yaml

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
    for file_mapping in files_mapping.keys():
        if fnmatch(file, file_mapping):
            return file_mapping
    return ""


def generate_run_mapping(files_mapping: dict, changed_files: list, run_files: list) -> dict:
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

        matched_mapping = get_mapping_by_wildcard(files_mapping, file_name)
        if matched_mapping:
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


def generate_run_mapping_inventory(diff_inventory: dict, playbooks: list) -> dict:
    '''Get the data for run ansible-playbook command

       args:
           diff_inventory: dict with groups as keys and hosts of these
                                 groups as values

           playbooks: list of filepaths to playbooks

       return: dict with playbook names as keys and limits/tags as values.
               Should be used as source for ansible-playbook command
    '''
    inventory_mapping = defaultdict(lambda: {"limits": set(), "tags": set()})
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
    commands = []
    for file_name, opts in run_mapping.items():
        limits = ",".join(opts["limits"])
        command = f'./{file_name} -l {limits}'

        if len(opts["tags"]):
            tags = ",".join(opts["tags"])
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


def get_files_mapping(mapping_file: str = 'tools/ci-files-mapping.yml') -> dict:
    '''Get mappings from mapping file

       Tries to import mapping file and convert it into python dictionary.
       Mapping file should look like:

           users_vault.yml:
             playbooks/configuration/run-server-common.yml:
               - users
               - ssh_keys

       so after loading it will be a dict of dicts.

       args:
           mapping_file: path to the file with mappings

       return: dict with mappings
    '''
    with open(mapping_file, "rt", encoding='utf-8') as f_hand:
        files_mapping = yaml.safe_load(f_hand)
    return files_mapping


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
    return changed_files


def apply(target_branch: str, dry_run: bool = False):
    '''Apply changes for given branch

       Given target branch, apply changes implemented on it.

       args:
           target_branch: reflog element, like commit hash or branch name

           dry_run: whether to really apply changes or just print what's needed
                    to be ran
    '''
    files_mapping = get_files_mapping()
    playbooks = get_playbooks()
    changed_files = get_changed_files(target_branch)
    run_mapping = generate_run_mapping(files_mapping, changed_files, playbooks)

    changed_inventory = get_inventory_files(changed_files)
    if changed_inventory:
        inventory_difference = difference_inventory(
                target_branch, changed_inventory)
        run_mapping_inventory = generate_run_mapping_inventory(
                inventory_difference, playbooks)
        run_mapping.update(run_mapping_inventory)

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

    arguments = arg_parser.parse_known_args()[0]

    if arguments.preview:
        apply(arguments.target_branch, dry_run=True)
    if arguments.apply:
        apply(arguments.target_branch)
