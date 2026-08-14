# Скрипты tools/

Все вспомогательные скрипты в каталоге [`tools/`](../../tools/).

## Shell-скрипты

| Скрипт | Назначение | Вызов |
|--------|------------|-------|
| `prepare.sh` | uv, `.venv`, poetry, daemon deps | `make prepare` или `bash tools/prepare.sh [PYTHON_VERSION]` |
| `set-vars.sh` | become, vault, mitogen env | `. ./tools/set-vars.sh` |
| `get-roles.sh` | ansible-galaxy install | `./tools/get-roles.sh [role ...]` |
| `select-hosts.sh` | fzf → comma-separated hosts | `bash tools/select-hosts.sh` (из Makefile) |
| `nodes_list.sh` | Таблица хостов | `./tools/nodes_list.sh` |
| `get-vault-pass` | Echo vault password | Через `ansible.cfg` vault_identity_list |

## Python-скрипты

| Скрипт | Назначение | Вызов |
|--------|------------|-------|
| `ci-script.py` | CI: diff → roles → ansible | `python tools/ci-script.py --preview --target_branch main` |
| `auto-format.py` | YAML cleanup в vars | `python tools/auto-format.py` |
| `import_infra_to_sshconf.py` | SSH config из host_vars | `./tools/import_infra_to_sshconf.py --help` |
| `export_hostvars_to_yaml.py` | Экспорт main.yml | `python tools/export_hostvars_to_yaml.py` |

## Ansible-плейбуки в tools/

| Файл | Назначение |
|------|------------|
| `switch-to-mitogen.yml` | Установка mitogen в `library/` |

```bash
ansible-playbook tools/switch-to-mitogen.yml
```

## Конфигурация

| Файл | Назначение |
|------|------------|
| `ci-config.yml` | Маппинг vars → playbooks для CI |
| `requirements.txt` | Зависимости для ci-script и tooling |
| `roles_lists/*.yml` | Списки Galaxy-ролей |

## get-roles.sh — детали

```bash
# Все списки (долго, ~97 файлов)
./tools/get-roles.sh

# По имени файла в roles_lists
./tools/get-roles.sh traefik.yml
./tools/get-roles.sh traefik

# Несколько
./tools/get-roles.sh traefik docker server-common
```

Роли устанавливаются в `./roles/` (`ansible-galaxy install -f -r ... -p ./roles/`).

## set-vars.sh — детали

- Требует **source** (`. ./tools/set-vars.sh`)
- На macOS нужен `greadlink` (`brew install coreutils`)
- Пароли хранятся в env текущей shell-сессии

## ci-script.py — флаги

| Флаг | Описание |
|------|----------|
| `--preview` | Показать команды (с `--target_branch`) |
| `--apply` | Выполнить команды |
| `--preview-manual "..."` | Ручной preview |
| `--apply-manual "..."` | Ручной apply |
| `--target_branch BRANCH` | База для git diff |

См. [ci-automation.md](../guides/ci-automation.md).

## prepare.sh — детали

- Устанавливает `uv` при отсутствии
- Создаёт `.venv` с Python 3.12 (или `PYTHON` из Makefile)
- Ставит poetry и `daemon/requirements.txt`

Поддержка: macOS, Linux (apt для python3).
