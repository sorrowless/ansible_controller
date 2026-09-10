# Провижининг-демон

Легковесный REST API в [`daemon/main.py`](../../daemon/main.py) для автоматического провижининга: принимает JSON, пишет `host_vars/` и `inventory/hosts`, запускает `ansible-playbook` в фоне.

**Полная документация:** [`daemon/readme.md`](../../daemon/readme.md) (архитектура, алгоритмы, curl-примеры).

## Запуск

```bash
make daemon
# или
make prepare
. .venv/bin/activate
uvicorn main:app --app-dir daemon --host 127.0.0.1 --port 8000
```

Переменные:

```bash
DAEMON_HOST=0.0.0.0 DAEMON_PORT=9000 make daemon
```

Swagger UI: `http://127.0.0.1:8000/docs`

## Эндпоинт POST /deploy

Принимает `DeployRequest`: hostname, ip_address, credentials, metadata, labels.

Действия:

1. Создаёт/обновляет `host_vars/<hostname>/main.yml` и `node-exporter.yml`
2. Добавляет хост в `inventory/hosts` (группа `test_hosts`)
3. В фоне запускает `playbooks/exporters/run-exporter-node.yml -l <hostname>`
4. Логи — в `logs/<hostname>_<timestamp>.log`

Ответ: `202 Accepted` (не ждёт завершения playbook).

## Минимальный curl

```bash
curl -X POST http://127.0.0.1:8000/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "test-vm-01",
    "ip_address": "192.168.1.100",
    "credentials": {
      "ansible_user": "root",
      "ansible_password": "secret"
    },
    "metadata": {
      "placement": "DC1",
      "company": "ACME"
    },
    "labels": ["env=prod"]
  }'
```

Больше примеров — в [`daemon/readme.md`](../../daemon/readme.md).

## Планы изменений демона

[`daemon/plans/`](../../daemon/plans/) — конвенция как в [`plans/README.md`](../../plans/README.md).

## Зависимости

[`daemon/requirements.txt`](../../daemon/requirements.txt) — FastAPI, uvicorn, pydantic, pyyaml. Устанавливаются через `make prepare`.
