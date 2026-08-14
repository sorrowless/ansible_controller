# Пример: минимальная настройка сервера

Развёртывание базового стека через composite-плейбук [`playbooks/run-minimal-full.yml`](../../playbooks/run-minimal-full.yml).

## Что устанавливается

Цепочка `import_playbook`:

1. pw-policy
2. server-common (пользователи, пакеты)
3. iptables
4. sshd
5. sudoers
6. atop
7. restart-docker

Теги: `security`, `common`, `iptables`, `sshd`, `sudoers`, `atop`.

## Подготовка

```bash
make prepare
. ./tools/set-vars.sh
```

## host_vars

Создайте каталог хоста с минимальным набором vars. Образцы:

- [`host_vars/.examples/idp.domain.com/server-common.yml`](../../host_vars/.examples/idp.domain.com/server-common.yml)
- [`host_vars/.examples/idp.domain.com/iptables.yml`](../../host_vars/.examples/idp.domain.com/iptables.yml)

Минимальный пример `host_vars/myhost.example.com/server-common.yml`:

```yaml
---
server_common_host:
  dns_hostname: "myhost.example.com"
```

Добавьте хост в `inventory/hosts` в группы, соответствующие плейбукам (`configuration/*`, `services/atop`).

## Роли

```bash
./tools/get-roles.sh server-common pw-policy iptables sshd sudoers atop
```

Или по одному имени, если файлы roles_lists совпадают.

## Запуск

Полный стек:

```bash
./playbooks/run-minimal-full.yml -l myhost.example.com
```

Только common-часть:

```bash
./playbooks/run-minimal-full.yml -l myhost.example.com --tags common
```

Только sshd:

```bash
./playbooks/run-minimal-full.yml -l myhost.example.com --tags sshd
```

## Проверка

```bash
./tools/nodes_list.sh
ansible myhost.example.com -m ping
```

## См. также

- [running-playbooks.md](../guides/running-playbooks.md) — теги и composite
- [configuring-hosts.md](../guides/configuring-hosts.md) — inventory и groups
