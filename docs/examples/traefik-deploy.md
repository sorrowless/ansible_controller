# Пример: деплой Traefik

Развёртывание reverse-proxy Traefik на хосте через Make или прямой вызов плейбука.

## Файлы в репозитории

| Файл | Назначение |
|------|------------|
| [`playbooks/services/run-traefik.yml`](../../playbooks/services/run-traefik.yml) | Плейбук |
| [`tools/roles_lists/traefik.yml`](../../tools/roles_lists/traefik.yml) | Galaxy-роль |
| [`host_vars/.examples/idp.domain.com/traefik.yml`](../../host_vars/.examples/idp.domain.com/traefik.yml) | Пример vars |
| [`host_vars/.examples/idp.domain.com/docker.yml`](../../host_vars/.examples/idp.domain.com/docker.yml) | Docker (часто нужен вместе) |

## Шаг 1: inventory

В [`inventory/hosts`](../../inventory/hosts):

```ini
[traefik]
myhost.example.com ansible_host=203.0.113.10

[docker_hosts]
myhost.example.com
```

Группа `traefik` обязательна — в плейбуке `hosts: traefik`.

## Шаг 2: host_vars

```bash
mkdir -p host_vars/myhost.example.com
cp host_vars/.examples/idp.domain.com/traefik.yml host_vars/myhost.example.com/
cp host_vars/.examples/idp.domain.com/docker.yml host_vars/myhost.example.com/
```

Отредактируйте:

- `traefik_web_host`, `traefik_swarm_manager`
- сети Docker (`traefik_docker_networks`)
- ACME / TLS (`traefik_environment_vars` с vault-ссылками)

## Шаг 3: окружение и роли

```bash
. ./tools/set-vars.sh
./tools/get-roles.sh traefik docker
```

## Шаг 4: запуск

**Через Make:**

```bash
HOST=myhost.example.com make traefik
```

**Напрямую:**

```bash
./playbooks/services/run-traefik.yml -l myhost.example.com
```

**Интерактивный выбор хоста (fzf):**

```bash
make traefik
```

## Переменные Make

```bash
# Несколько хостов
HOST=web01.example.com,web02.example.com make traefik

# Демон на другом порту (не связано с traefik, для справки)
DAEMON_PORT=9000 make daemon
```

## Связанные сервисы

Часто Traefik ставят вместе с TLS и nginx — см. composite `run-*-full.yml` или отдельные плейбуки `run-tls.yml`, `run-nginx.yml`.

## См. также

- [makefile-targets.md](../reference/makefile-targets.md)
- [getting-started.md](../guides/getting-started.md)
