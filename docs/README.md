# Документация Ansible Controller

Навигация по документации репозитория. Краткий вход — [`README.md`](../README.md) в корне. Для AI-агентов — [`AGENTS.md`](../AGENTS.md).

## Архитектура

| Документ | Описание |
|----------|----------|
| [repository-layout.md](architecture/repository-layout.md) | Дерево каталогов и назначение каждого |
| [deployment-flow.md](architecture/deployment-flow.md) | Цепочка host_vars → roles → playbook |

## Руководства

| Документ | Описание |
|----------|----------|
| [getting-started.md](guides/getting-started.md) | Первый деплой от нуля |
| [configuring-hosts.md](guides/configuring-hosts.md) | inventory, host_vars, group_vars, vars/ |
| [running-playbooks.md](guides/running-playbooks.md) | Запуск плейбуков, теги, composite |
| [make-and-tools.md](guides/make-and-tools.md) | Makefile и скрипты tools/ |
| [ci-automation.md](guides/ci-automation.md) | ci-script.py и ci-config.yml |
| [provisioner-daemon.md](guides/provisioner-daemon.md) | REST-демон; детали в [daemon/readme.md](../daemon/readme.md) |

## Справочник

| Документ | Описание |
|----------|----------|
| [makefile-targets.md](reference/makefile-targets.md) | Таргеты `make help` |
| [tools-scripts.md](reference/tools-scripts.md) | Все скрипты в tools/ |
| [playbooks-catalog.md](reference/playbooks-catalog.md) | Категории плейбуков и composite |
| [roles-lists.md](reference/roles-lists.md) | roles_lists и get-roles.sh |
| [ansible-configuration.md](reference/ansible-configuration.md) | ansible.cfg, vault, extra vars |

## Примеры сценариев

| Документ | Описание |
|----------|----------|
| [minimal-server.md](examples/minimal-server.md) | Базовая настройка сервера |
| [traefik-deploy.md](examples/traefik-deploy.md) | Деплой Traefik |
| [monitoring-stack.md](examples/monitoring-stack.md) | Стек мониторинга |

Живые YAML-примеры переменных — [`host_vars/.examples/`](../host_vars/.examples/).

## Планы работ

- Репозиторий: [`plans/README.md`](../plans/README.md)
- Демон: [`daemon/plans/`](../daemon/plans/)
