# Запуск плейбуков

Соглашения и способы вызова плейбуков в `playbooks/`.

## Паттерн run-*.yml

Большинство плейбуков:

1. Исполняемы как скрипт (shebang `ansible-playbook`)
2. Подключают [`vars/extra.yaml`](../../vars/extra.yaml)
3. Вызывают **одну** Galaxy-роль

Пример [`playbooks/services/run-traefik.yml`](../../playbooks/services/run-traefik.yml):

```yaml
#!/usr/bin/env -S ansible-playbook -e @vars/extra.yaml
---
- name: Configure target servers
  hosts: traefik
  become: yes
  roles:
    - { role: sorrowless.traefik, tags: ['traefik'] }
```

Запуск:

```bash
. ./tools/set-vars.sh
./tools/get-roles.sh traefik
./playbooks/services/run-traefik.yml -l myhost.example.com
```

Эквивалент без shebang:

```bash
ansible-playbook -e @vars/extra.yaml playbooks/services/run-traefik.yml -l myhost.example.com
```

## Лимит хостов (-l)

Всегда указывайте `-l` для production-хостов:

```bash
./playbooks/services/run-docker-services.yml -l host1,host2
```

Несколько хостов — через запятую без пробелов.

## Теги (--tags)

```bash
./playbooks/configuration/run-server-common.yml -l myhost --tags users
./playbooks/run-minimal-full.yml -l myhost --tags common,sshd
```

Теги заданы в ролях и в composite-плейбуках.

## Composite-стеки (run-*-full.yml)

В **корне** `playbooks/` лежат композитные плейбуки — цепочки `import_playbook`:

| Файл | Назначение |
|------|------------|
| `run-minimal-full.yml` | Базовый сервер: pw-policy, common, iptables, sshd, sudoers, atop |
| `run-mail-full.yml` | Почтовый стек |
| `run-prometheus-full.yml` | Prometheus |
| `run-exporters-full.yml` | Набор exporters |
| `run-vault-full.yml` | HashiCorp Vault |
| … | Всего 19 файлов `run-*-full.yml` |

Пример фрагмента `run-minimal-full.yml`:

```yaml
- name: Execute common tasks
  import_playbook: configuration/run-server-common.yml
  tags:
    - common
```

Запуск всего стека:

```bash
./playbooks/run-minimal-full.yml -l myhost.example.com
```

Частичный запуск по тегам:

```bash
./playbooks/run-minimal-full.yml -l myhost --tags iptables
```

## Категории плейбуков

| Каталог | Назначение |
|---------|------------|
| `configuration/` | Базовая настройка ОС (sshd, iptables, java, pyenv) |
| `services/` | Приложения и сервисы (traefik, docker, gitlab, …) |
| `exporters/` | Prometheus exporters |
| `monitoring/` | Grafana, VictoriaMetrics, Sensu, … |
| `databases/` | PostgreSQL, Redis, Patroni, … |
| `backups/` | Резервное копирование |
| `logs/` | Fluentd, Graylog, VictoriaLogs |
| `vpns/` | OpenVPN, WireGuard, IPsec |
| `utils/` | apt-update, ping, desktop, restart-docker |

Полный обзор — [playbooks-catalog.md](../reference/playbooks-catalog.md).

## Поиск плейбука

```bash
find playbooks -name 'run-*.yml' | sort
find playbooks -name '*traefik*'
```

## Перед запуском

1. `. ./tools/set-vars.sh`
2. `./tools/get-roles.sh <нужные-роли>`
3. Хост в inventory и в `host_vars/`
4. При необходимости — `make prepare` (для плейбуков через Make)

## Make vs прямой вызов

Make-таргеты (`make traefik`, `make docker-services`) — обёртки с автоматическим `-l` из `HOST` или fzf. Полный список — [makefile-targets.md](../reference/makefile-targets.md).

Не все плейбуки есть в Makefile; для остальных — прямой вызов `./playbooks/.../run-*.yml`.
