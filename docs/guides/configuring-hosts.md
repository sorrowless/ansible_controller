# Настройка хостов и переменных

Как связаны `inventory/`, `host_vars/`, `group_vars/` и `vars/`.

## inventory/hosts

Основной инвентарь задаётся в [`ansible.cfg`](../ansible.cfg):

```ini
inventory = inventory/hosts
```

Файл [`inventory/hosts`](../inventory/hosts) создаётся **вручную** (см. [`inventory/testing.hosts.example`](../inventory/testing.hosts.example)).

Типичная структура:

```ini
[traefik]
myhost.example.com ansible_host=203.0.113.10

[docker_hosts]
myhost.example.com
```

Группы (`traefik`, `docker_hosts`, …) должны соответствовать `hosts:` в плейбуках.

Дополнительно в `inventory/`:

| Файл | Назначение |
|------|------------|
| `iac_state_inventory.py` | Динамический инвентарь (при необходимости) |
| `host_vars`, `group_vars` | Симлинки/наследование Ansible (если используются) |

## host_vars/

Каталог `host_vars/<hostname>/` — переменные для конкретного хоста.

- Имя каталога = hostname из inventory (FQDN).
- Внутри — один или несколько YAML-файлов по сервисам: `traefik.yml`, `docker.yml`, `server-common.yml`.
- Имя файла обычно совпадает с файлом в `tools/roles_lists/<имя>.yml`.

**Примеры:** [`host_vars/.examples/`](../host_vars/.examples/) — готовые конфиги (каталоги `.examples`, `.DEPRECATED` не участвуют в `make` / fzf).

Скрытые каталоги в `host_vars/` (начинаются с `.`) исключаются из `tools/select-hosts.sh`.

## group_vars/

Групповые переменные для Ansible-групп из inventory.

Примеры в репозитории:

- `group_vars/all/system.yml` — общие настройки
- `group_vars/docker_hosts/docker.yml` — для группы docker-хостов
- `group_vars/.all.yml.example` — шаблон локального `all.yml` (в gitignore)

Локальный `group_vars/all.yml` в `.gitignore` — для секретов и переопределений.

## vars/

Общие переменные, подключаемые плейбуками:

```yaml
# vars/extra.yaml
ansible_become_pass: "{{ lookup('env', 'ANSIBLE_BECOME_PASS') }}"
ansible_vault_pass: "{{ lookup('env', 'ANSIBLE_VAULT_REAL_PASS') }}"
```

Большинство `run-*.yml` начинаются с shebang:

```bash
#!/usr/bin/env -S ansible-playbook -e @vars/extra.yaml
```

Поэтому перед запуском нужен `. ./tools/set-vars.sh`.

## Связь с ролями и плейбуками

```
host_vars/myhost/traefik.yml  →  tools/roles_lists/traefik.yml  →  playbooks/services/run-traefik.yml
```

Плейбук `run-traefik.yml` использует `hosts: traefik` и роль `sorrowless.traefik`. Хост должен быть в группе `[traefik]`, переменные — в `host_vars/myhost/traefik.yml`.

## Полезные команды

```bash
./tools/nodes_list.sh                              # список хостов
python tools/export_hostvars_to_yaml.py            # экспорт main.yml
./tools/import_infra_to_sshconf.py --help          # SSH config из host_vars
python tools/auto-format.py                        # форматирование YAML в vars
```

## Демон и автоматический host_vars

REST API (`daemon/main.py`) при `POST /deploy` создаёт:

- `host_vars/<hostname>/main.yml`
- `host_vars/<hostname>/node-exporter.yml`
- запись в `inventory/hosts` (группа `test_hosts`)

См. [provisioner-daemon.md](provisioner-daemon.md) и [`daemon/readme.md`](../../daemon/readme.md).
