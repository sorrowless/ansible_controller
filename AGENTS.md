# Инструкции для AI-агента

Ansible Controller — каркас для деплоя ПО на удалённые машины через Ansible. Репозиторий содержит плейбуки, переменные хостов, инструменты (`tools/`), Makefile-обёртки и REST-демон (`daemon/`) для оркестрации локальных запусков `ansible-playbook`.

## Обязательный порядок чтения

Перед любыми изменениями:

1. Этот файл — [`AGENTS.md`](AGENTS.md)
2. Навигация по документации — [`docs/README.md`](docs/README.md)
3. Релевантный guide или reference из таблицы ниже
4. Для `daemon/` — [`daemon/readme.md`](daemon/readme.md) и при необходимости [`daemon/plans/`](daemon/plans/)
5. Для планируемых задач — [`plans/README.md`](plans/README.md)

## Маршрутизация: задача → документация

| Задача | Куда смотреть |
|--------|----------------|
| Обзор структуры репозитория | [`docs/architecture/repository-layout.md`](docs/architecture/repository-layout.md) |
| Как устроен деплой end-to-end | [`docs/architecture/deployment-flow.md`](docs/architecture/deployment-flow.md) |
| Первый запуск, bootstrap | [`docs/guides/getting-started.md`](docs/guides/getting-started.md) |
| inventory, host_vars, group_vars | [`docs/guides/configuring-hosts.md`](docs/guides/configuring-hosts.md) |
| Запуск плейбуков, теги, composite | [`docs/guides/running-playbooks.md`](docs/guides/running-playbooks.md) |
| Makefile, set-vars, get-roles | [`docs/guides/make-and-tools.md`](docs/guides/make-and-tools.md) |
| CI: diff → роли → ansible | [`docs/guides/ci-automation.md`](docs/guides/ci-automation.md) |
| REST-демон провижининга | [`docs/guides/provisioner-daemon.md`](docs/guides/provisioner-daemon.md), [`daemon/readme.md`](daemon/readme.md) |
| Таргеты Make | [`docs/reference/makefile-targets.md`](docs/reference/makefile-targets.md) |
| Скрипты в tools/ | [`docs/reference/tools-scripts.md`](docs/reference/tools-scripts.md) |
| Каталог плейбуков | [`docs/reference/playbooks-catalog.md`](docs/reference/playbooks-catalog.md) |
| roles_lists и Galaxy | [`docs/reference/roles-lists.md`](docs/reference/roles-lists.md) |
| ansible.cfg, vault, extra vars | [`docs/reference/ansible-configuration.md`](docs/reference/ansible-configuration.md) |
| Пошаговые сценарии | [`docs/examples/`](docs/examples/) |
| Примеры YAML хостов | [`host_vars/.examples/`](host_vars/.examples/) |

## Конвенции

- **Документация** — в `docs/`, component-readme (`daemon/readme.md`) или `host_vars/.examples/`. Не дублировать длинные описания в коде.
- **Планы** — `plans/` (репозиторий) или `daemon/plans/` (демон); формат в [`plans/README.md`](plans/README.md).
- **Роли** — не коммитятся (`roles/` в `.gitignore`); списки в `tools/roles_lists/`, установка через `./tools/get-roles.sh`.
- **Плейбуки** — один `run-*.yml` обычно вызывает одну Galaxy-роль; composite — `playbooks/run-*-full.yml` в корне `playbooks/`.
- **CI-маппинг** — [`tools/ci-config.yml`](tools/ci-config.yml) (не `ci-files-mapping.yml`).

## Быстрые факты

- Инвентарь по умолчанию: `inventory/hosts` ([`ansible.cfg`](ansible.cfg))
- Пароль vault: `tools/get-vault-pass` (переменная `ANSIBLE_VAULT_REAL_PASS`)
- Become/vault для плейбуков: `vars/extra.yaml` + `. ./tools/set-vars.sh`
- Make-таргеты с хостами: `HOST=...` или интерактивный `fzf` через `tools/select-hosts.sh`
