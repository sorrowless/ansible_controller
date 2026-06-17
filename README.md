# sbog.controller

Base framework to create further Ansible deploys for organization. It's nothing
more but just a carcass to further developing deployments.

#### Requirements

Ansible Galaxy

#### Dependencies

None

#### Base usage

This will install all needed roles to `roles` directory:

```bash
./tools/get-roles.sh
```

Then you just need to create according group/host vars, inventory files and run
your playbooks.
In case you just need to know current nodes list, run

```bash
./tools/nodes_list.sh
```

Some examples can be found in `host_vars/.examples` directory.
In case you want to faster deploys there is a playbook which downloads mitogen
and installed it locally and configures as default strategy. You can run it by

```bash
ansible-playbook tools/switch-to-mitogen.yml
```

#### Make / interactive deploys

The root `Makefile` wraps common deploy targets. `make prepare` bootstraps the virtualenv and installs dependencies from `daemon/requirements.txt` (FastAPI, uvicorn, and related packages).

Host-specific targets (`docker-services`, `traefik`) accept an optional `HOST` variable. When `HOST` is not set, `fzf` prompts for one or more hosts from top-level `host_vars/` directories (hidden dirs like `.examples` and `.DEPRECATED` are excluded).

`fzf` is only required for interactive mode (`brew install fzf` on macOS).

```bash
# Start the Ansible provisioner API (Swagger UI at /docs)
make daemon

# Override bind address/port
DAEMON_HOST=0.0.0.0 DAEMON_PORT=9000 make daemon

# Interactive: pick host(s) with fzf (Tab to multi-select, Enter to confirm)
make docker-services

# Single host
HOST=ru01.sbog.org make traefik

# Multiple hosts (comma-separated, passed to ansible -l)
HOST=ru01.sbog.org,us03.sbog.org make docker-services

# Reuse HOST across commands in the same shell
export HOST=router-pc.sbog.org
make traefik
```

For a tabular list of hosts with IP and placement metadata, use `./tools/nodes_list.sh`.

API details and `curl` examples for the provisioner daemon are in [`daemon/readme.md`](daemon/readme.md).

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

Playbooks in every directory run exactly one included role. But full-files
includes entire run-files from subdirectories.

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

[Stan Bogatkin](https://sbog.org)
