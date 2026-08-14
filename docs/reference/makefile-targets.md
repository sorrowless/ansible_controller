# Таргеты Makefile

Источник истины — [`Makefile`](../../Makefile). Актуальный список:

```bash
make help
```

## Таблица таргетов

| Таргет | Зависимости | Команда |
|--------|-------------|---------|
| `help` | — | Вывод справки |
| `prepare` | — | `bash tools/prepare.sh` |
| `daemon` | `prepare` | uvicorn `daemon/main.py` |
| `sshconfig` | `prepare` | `./playbooks/utils/run-desktop.yml -c 'localhost,' -t sshconfig` |
| `docker-services` | `prepare` | `./playbooks/services/run-docker-services.yml -l $HOST` |
| `traefik` | `prepare` | `./playbooks/services/run-traefik.yml -l $HOST` |

## Переменные окружения

| Переменная | Default | Использование |
|------------|---------|---------------|
| `VENV` | `.venv` | Путь к virtualenv (в Makefile) |
| `PYTHON` | `3.12` | Версия для `prepare.sh` |
| `HOST` | fzf | Лимит хостов для deploy-таргетов |
| `DAEMON_HOST` | `127.0.0.1` | Bind демона |
| `DAEMON_PORT` | `8000` | Порт демона |

## Макрос run_with_host

Для `docker-services` и `traefik`:

1. Если `HOST` не задан — вызывается `bash tools/select-hosts.sh` (fzf)
2. Активируется `.venv`
3. Плейбук запускается с `-l $HOST`

## Примеры

```bash
make prepare
make daemon
make sshconfig
make docker-services                              # fzf
HOST=web01.example.com make traefik
HOST=web01,web02 make docker-services
DAEMON_PORT=9000 make daemon
```

Плейбуки без Make-таргета запускаются напрямую — см. [running-playbooks.md](../guides/running-playbooks.md).
