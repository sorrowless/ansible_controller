# Makefile и инструменты tools/

## Makefile

Корневой [`Makefile`](../../Makefile) оборачивает частые операции. Список таргетов:

```bash
make help
```

| Таргет | Действие |
|--------|----------|
| `prepare` | `tools/prepare.sh` — uv, `.venv`, poetry, daemon deps |
| `daemon` | uvicorn для `daemon/main.py` |
| `sshconfig` | `playbooks/utils/run-desktop.yml` на localhost |
| `docker-services` | `run-docker-services.yml` с `-l $HOST` |
| `traefik` | `run-traefik.yml` с `-l $HOST` |

### Переменные

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `HOST` | (fzf) | Один или несколько хостов через запятую |
| `PYTHON` | `3.12` | Версия Python для venv |
| `DAEMON_HOST` | `127.0.0.1` | Bind address демона |
| `DAEMON_PORT` | `8000` | Порт демона |

### Выбор хоста

```bash
# Интерактивно (fzf, Tab — мультивыбор)
make traefik

# Один хост
HOST=ru01.example.com make docker-services

# Несколько хостов
HOST=host1,host2 make traefik

# В текущей shell-сессии
export HOST=myhost.example.com
make traefik
```

`tools/select-hosts.sh` читает каталоги в `host_vars/`, исключая `.examples` и скрытые.

## set-vars.sh

Интерактивная настройка окружения для Ansible:

```bash
. ./tools/set-vars.sh
```

Устанавливает:

- `ANSIBLE_BECOME_PASS`
- `ANSIBLE_VAULT_REAL_PASS` → `tools/get-vault-pass`
- при наличии mitogen в `library/` — `ANSIBLE_STRATEGY=mitogen_linear`

## get-roles.sh

Установка Galaxy-ролей в `./roles/`:

```bash
./tools/get-roles.sh                    # все roles_lists (долго)
./tools/get-roles.sh traefik            # по имени файла
./tools/get-roles.sh traefik server-common docker
```

Поиск по подстроке, если точного файла нет: `traefik` → `tools/roles_lists/traefik.yml`.

## nodes_list.sh

Таблица хостов из `host_vars/`:

```bash
./tools/nodes_list.sh
```

## prepare.sh

Вызывается из `make prepare`. Ставит `uv`, создаёт `.venv`, poetry, pip-зависимости демона.

## switch-to-mitogen.yml

Плейбук (не shell-скрипт):

```bash
ansible-playbook tools/switch-to-mitogen.yml
```

Клонирует mitogen в `library/` (gitignored).

## Прочие скрипты

Полная таблица — [tools-scripts.md](../reference/tools-scripts.md).

| Скрипт | Кратко |
|--------|--------|
| `ci-script.py` | CI: diff → роли → ansible-команды |
| `auto-format.py` | Форматирование YAML в vars |
| `import_infra_to_sshconf.py` | Генерация `~/.ssh/config` |
| `export_hostvars_to_yaml.py` | Экспорт host_vars |

## Типичный рабочий цикл

```bash
make prepare
. ./tools/set-vars.sh
./tools/get-roles.sh traefik docker
HOST=myhost.example.com make traefik
```
