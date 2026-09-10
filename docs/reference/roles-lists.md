# roles_lists и установка ролей

Galaxy-роли **не хранятся в git**. Списки зависимостей — в [`tools/roles_lists/`](../../tools/roles_lists/) (~97 YAML-файлов).

## Формат файла roles_lists

Типичный [`tools/roles_lists/traefik.yml`](../../tools/roles_lists/traefik.yml):

```yaml
- src: sorrowless.traefik
  version: master
```

Некоторые файлы содержат несколько ролей (например `gitlab.yml`, `vault.yml`).

## Связь с host_vars

| host_vars | roles_lists | playbook |
|-----------|-------------|----------|
| `host_vars/myhost/traefik.yml` | `tools/roles_lists/traefik.yml` | `playbooks/services/run-traefik.yml` |
| `host_vars/myhost/docker.yml` | `tools/roles_lists/docker.yml` | `playbooks/services/run-docker.yml` |
| `host_vars/myhost/server-common.yml` | `tools/roles_lists/server-common.yml` | `playbooks/configuration/run-server-common.yml` |

Имя YAML в `host_vars/<hostname>/` обычно совпадает с basename файла в `roles_lists/`.

## get-roles.sh

```bash
./tools/get-roles.sh traefik
```

Алгоритм:

1. Если `tools/roles_lists/traefik.yml` существует — использовать его
2. Иначе — поиск по подстроке среди `*.yml` в `roles_lists/`
3. `ansible-galaxy install -f -r <file> -p ./roles/`

Без аргументов — перебор **всех** файлов (долго, для полного mirror).

## Группы ролей (обзор)

| Область | Примеры файлов roles_lists |
|---------|---------------------------|
| База | server-common, sshd, iptables, sudoers, pw-policy |
| Docker / proxy | docker, docker_services, traefik, nginx-service, haproxy |
| БД | postgresql, mariadb, redis-db, patroni, mongodb |
| Мониторинг | grafana, victoriametrics, vmagent, alertmanager, sensu |
| Exporters | exporter-node, exporter-blackbox, exporter-nginx, … |
| Логи | fluentd, graylog, vlinsert, vlselect, vlstorage |
| VPN | openvpn, wireguardvpn, ipsecvpn |
| Приложения | gitlab, jenkins, harbor, bitwarden, vault, … |

Полный список:

```bash
ls tools/roles_lists/*.yml
```

## CI и роли

`ci-script.py` по изменённым vars-файлам определяет соответствующие `roles_lists` и вызывает `ansible-galaxy install` перед playbook.

## roles/ каталог

После установки роли появляются в `./roles/` (в `.gitignore`). `ansible.cfg`:

```ini
roles_path = roles
```
