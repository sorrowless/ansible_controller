# Каталог плейбуков

Плейбуки в [`playbooks/`](../../playbooks/). Именование: `run-<service>.yml`.

## Категории (подкаталоги)

| Каталог | Примерные run-*.yml | Назначение |
|---------|---------------------|------------|
| `configuration/` | run-sshd, run-iptables, run-java | Базовая настройка ОС |
| `services/` | run-traefik, run-docker, run-gitlab | Приложения и сервисы |
| `exporters/` | run-exporter-node, run-exporter-blackbox | Prometheus exporters |
| `monitoring/` | run-grafana, run-victoriametrics | Мониторинг |
| `databases/` | run-postgresql, run-redis-db | СУБД |
| `backups/` | run-backup, run-rsnapshot | Резервное копирование |
| `logs/` | run-fluentd, run-graylog | Логирование |
| `vpns/` | run-openvpn, run-wireguardvpn | VPN |
| `utils/` | run-ping, run-desktop, run-apt-update | Утилиты |

Точное количество файлов меняется; актуальный список:

```bash
find playbooks -mindepth 2 -name 'run-*.yml' | wc -l
find playbooks -mindepth 2 -name 'run-*.yml' | sort
```

## Composite-стеки (корень playbooks/)

Файлы `run-*-full.yml` объединяют несколько плейбуков через `import_playbook`:

| Файл |
|------|
| `run-minimal-full.yml` |
| `run-bitwarden-full.yml` |
| `run-davical-full.yml` |
| `run-mail-full.yml` |
| `run-ttrss-full.yml` |
| `run-exporters-full.yml` |
| `run-youtrack-full.yml` |
| `run-jenkins-full.yml` |
| `run-wireguardvpn-full.yml` |
| `run-rsnapshot-backup-full.yml` |
| `run-vpn-bot-full.yml` |
| `run-elasticsearch-full.yml` |
| `run-prometheus-full.yml` |
| `run-graylog-full.yml` |
| `run-sensu-monitoring-full.yml` |
| `run-docker-registry-full.yml` |
| `run-vault-full.yml` |
| `run-vm-server-full.yml` |
| `run-syslog-full.yml` |

```bash
ls playbooks/run-*-full.yml
```

## Паттерн одного плейбука

```yaml
#!/usr/bin/env -S ansible-playbook -e @vars/extra.yaml
---
- name: Configure target servers
  hosts: <ansible_group>
  become: yes
  roles:
    - { role: <galaxy_role>, tags: ['<tag>'] }
```

## Связь с Makefile

Только часть плейбуков обёрнута в Make:

- `traefik` → `services/run-traefik.yml`
- `docker-services` → `services/run-docker-services.yml`
- `sshconfig` → `utils/run-desktop.yml`

Остальные — прямой вызов. См. [running-playbooks.md](../guides/running-playbooks.md).

## Поиск по имени

```bash
find playbooks -name '*postgres*'
find playbooks -name 'run-traefik.yml'
```

## Связь с roles_lists

Имя `run-foo.yml` обычно соответствует `tools/roles_lists/foo.yml` (с возможными вариациями в именовании, например `run-docker-services.yml` ↔ `docker_services.yml`).
