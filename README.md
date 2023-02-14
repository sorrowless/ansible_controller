sbog.controller
===============

Base framework to create further Ansible deploys for organization. It's nothing
more but just a carcass to further developing deployments.

#### Requirements

Ansible Galaxy

#### Dependencies

None

#### Base usage

This will install all needed roles to `roles` directory:

```
./tools/get-roles.sh
```

Then you just need to create according group/host vars, inventory files and run
your playbooks.
In case you just need to know current nodes list, run

```
./tools/nodes_list.sh
```

Some examples can be found in `host_vars/.examples` directory.
In case you want to faster deploys there is a playbook which downloads mitogen
and installed it locally and configures as default strategy. You can run it by

```
ansible-playbook tools/switch-to-mitogen.yml
```

#### Playbooks directory structure
The directory has the following structure:
- backups 
- configuration 
- databases 
- exporters 
- logs 
- monitoring 
- services 
- utils 
- vpns
- full-files

Playbooks in every directory run exactly one included role. But full-files includes entire run-files from subdirectories.

```yaml
# example run-bitwarden-full.yml
...
---
- name: Ensure TLS certificates
  import_playbook: services/run-tls.yml

- name: Setup Nginx
  import_playbook: services/run-nginx.yml
...
```
```yaml
# example services/run-tls.yml
...
---
- name: Configure target servers
  hosts: all
  #serial: 1
  remote_user: root

  roles:
    - { role: sorrowless.tls, tags: ['tls'] }
...
```

#### Gitlab-CI

Python script tools/ci-script.py check git diff for current branch and target branch (specified by option --target_branch). For changed host and group vars files that script find corresponding roles for thats files in tools/roles_lists directory and download it. Than scrip generate ansible commands with limits and tags. On option --preview script just show commands, on option --apply script will execute that commands. You can specify tags for generated commands and manualy match config files with run-files in tools/ci-files-mapping.yml.

```yaml
# example tools/ci-files-mapping.yml
scrape_configs_*.yml: # host/group vars file. You can use unix wildcards in conf-files names
  run-vmagent.yml: # run-file who will execute for that conf-faile
  - some-tag # tags for that run-file
```

#### License

Apache 2.0

#### Author Information

Stanislaw Bogatkin (https://sbog.ru)
