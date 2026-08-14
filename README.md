# Ansible Controller

Каркас для деплоя ПО на удалённые машины через Ansible: плейбуки, переменные хостов, скрипты (`tools/`), Makefile-обёртки и REST-демон для оркестрации локальных запусков `ansible-playbook`.

Полная документация: [`docs/README.md`](docs/README.md). Для AI-агентов: [`AGENTS.md`](AGENTS.md).

## Требования

| Компонент | Назначение |
|-----------|------------|
| Ansible + ansible-galaxy | Запуск плейбуков и установка ролей |
| `uv` | Создаётся через `make prepare` |
| `fzf` | Интерактивный выбор хостов в `make` (`brew install fzf`) |
| GNU readlink | Для `set-vars.sh` на macOS (`brew install coreutils`) |

## Быстрый старт

```bash
make prepare
. ./tools/set-vars.sh
./tools/get-roles.sh traefik server-common

# inventory/hosts — вручную; host_vars — по образцу host_vars/.examples/
mkdir -p host_vars/myhost.example.com
cp host_vars/.examples/idp.domain.com/traefik.yml host_vars/myhost.example.com/

./playbooks/services/run-traefik.yml -l myhost.example.com
```

Подробнее: [`docs/guides/getting-started.md`](docs/guides/getting-started.md).

## Структура репозитория

| Каталог | Назначение |
|---------|------------|
| [`playbooks/`](playbooks/) | Плейбуки по категориям + `run-*-full.yml` в корне |
| [`host_vars/`](host_vars/) | Переменные конкретных хостов; примеры в `.examples/` |
| [`group_vars/`](group_vars/) | Групповые переменные Ansible |
| [`inventory/`](inventory/) | Инвентарь (`hosts` создаётся вручную) |
| [`vars/`](vars/) | Общие extra vars (`extra.yaml` для shebang-плейбуков) |
| [`tools/roles_lists/`](tools/roles_lists/) | Списки Galaxy-ролей для `get-roles.sh` |
| [`tools/`](tools/) | Скрипты, CI, mitogen-плейбук |
| [`daemon/`](daemon/) | REST API провижининга |
| [`docs/`](docs/) | Документация |
| `roles/` | Скачанные роли (gitignored) |
| `library/` | mitogen после `switch-to-mitogen.yml` (gitignored) |

Детали: [`docs/architecture/repository-layout.md`](docs/architecture/repository-layout.md).

## Установка ролей

Роли не хранятся в git. Скачивание по спискам в `tools/roles_lists/`:

```bash
./tools/get-roles.sh traefik docker    # конкретные роли
./tools/get-roles.sh                   # все списки (долго)
```

См. [`docs/reference/roles-lists.md`](docs/reference/roles-lists.md).

## Make

```bash
make help
```

| Таргет | Описание |
|--------|----------|
| `prepare` | uv, `.venv`, зависимости демона |
| `daemon` | REST API (Swagger: `/docs`) |
| `sshconfig` | SSH config на localhost |
| `docker-services` | Деплой docker-services |
| `traefik` | Деплой Traefik |

`fzf` нужен только если `HOST` не задан. Скрытые каталоги в `host_vars/` (`.examples` и т.п.) не попадают в выбор.

```bash
make daemon
DAEMON_HOST=0.0.0.0 DAEMON_PORT=9000 make daemon

make docker-services                                    # fzf
HOST=ru01.example.com make traefik
HOST=ru01.example.com,us03.example.com make docker-services

export HOST=router.example.com
make traefik
```

Список хостов: `./tools/nodes_list.sh`.

## Плейбуки

Каталоги: `backups`, `configuration`, `databases`, `exporters`, `logs`, `monitoring`, `services`, `utils`, `vpns`.

Типичный плейбук — один `run-*.yml` на одну Galaxy-роль:

```yaml
#!/usr/bin/env -S ansible-playbook -e @vars/extra.yaml
---
- name: Configure target servers
  hosts: traefik
  roles:
    - { role: sorrowless.traefik, tags: ['traefik'] }
```

Композитные стеки — в корне `playbooks/` как `run-*-full.yml` (19 файлов), например `run-minimal-full.yml`, `run-mail-full.yml`:

```yaml
- name: Ensure TLS certificates
  import_playbook: services/run-tls.yml
```

```bash
./playbooks/run-minimal-full.yml -l myhost.example.com --tags common
find playbooks -name 'run-*.yml' | sort
```

Каталог: [`docs/reference/playbooks-catalog.md`](docs/reference/playbooks-catalog.md).

## Переменные и vault

```bash
. ./tools/set-vars.sh    # become + vault (+ mitogen если установлен)
```

Плейбуки подключают [`vars/extra.yaml`](vars/extra.yaml). Vault: `tools/get-vault-pass` через [`ansible.cfg`](ansible.cfg).

Примеры host vars: [`host_vars/.examples/`](host_vars/.examples/).

## Ускорение: mitogen

```bash
ansible-playbook tools/switch-to-mitogen.yml
. ./tools/set-vars.sh
```

## Демон провижининга

```bash
make daemon
```

API и `curl`-примеры: [`daemon/readme.md`](daemon/readme.md), [`docs/guides/provisioner-daemon.md`](docs/guides/provisioner-daemon.md).

## CI

Скрипт [`tools/ci-script.py`](tools/ci-script.py) анализирует git diff, скачивает роли и генерирует ansible-команды. Маппинг vars → playbooks: [`tools/ci-config.yml`](tools/ci-config.yml).

```bash
python tools/ci-script.py --preview --target_branch main
python tools/ci-script.py --apply --target_branch main
```

Пример маппинга в `ci-config.yml`:

```yaml
mappings:
  scrape_configs_*.yml:
    playbooks/monitoring/run-vmagent.yml: {}

  docker.yml:
    playbooks/services/run-docker.yml:
      priority: 30
```

См. [`docs/guides/ci-automation.md`](docs/guides/ci-automation.md).

## Примеры сценариев

| Сценарий | Документ |
|----------|----------|
| Минимальный сервер | [`docs/examples/minimal-server.md`](docs/examples/minimal-server.md) |
| Traefik | [`docs/examples/traefik-deploy.md`](docs/examples/traefik-deploy.md) |
| Мониторинг | [`docs/examples/monitoring-stack.md`](docs/examples/monitoring-stack.md) |

## Лицензия

Apache 2.0

## Автор

[Stan Bogatkin](https://sbog.org)
