# Структура репозитория

Ansible Controller — монорепозиторий конфигурации и инструментов для Ansible-деплоев. Роли Galaxy **не** хранятся в git; их скачивают по мере необходимости.

## Дерево каталогов

```
.
├── AGENTS.md              # Инструкции для AI-агента
├── README.md              # Краткий вход для человека
├── Makefile               # Обёртки над частыми командами
├── ansible.cfg            # Настройки Ansible по умолчанию
│
├── daemon/                # REST API для локального ansible-playbook
│   ├── main.py
│   ├── readme.md          # Подробная техдока демона
│   ├── requirements.txt
│   └── plans/             # Планы изменений демона
│
├── docs/                  # Общая документация (навигация: docs/README.md)
├── plans/                 # Планы изменений репозитория
│
├── playbooks/             # Ansible-плейбуки
│   ├── backups/
│   ├── configuration/
│   ├── databases/
│   ├── exporters/
│   ├── logs/
│   ├── monitoring/
│   ├── services/
│   ├── utils/
│   ├── vpns/
│   └── run-*-full.yml     # Композитные стеки (корень playbooks/)
│
├── inventory/             # Инвентарь Ansible
│   ├── hosts              # Основной файл (создаётся вручную)
│   └── testing.hosts.example
│
├── host_vars/             # Переменные конкретных хостов
│   └── .examples/         # Примеры конфигураций (не деплоятся)
│
├── group_vars/            # Групповые переменные
│   └── .all.yml.example
│
├── vars/                  # Общие extra vars для плейбуков
│   └── extra.yaml         # become/vault из env
│
├── tools/                 # Скрипты и вспомогательные плейбуки
│   ├── roles_lists/       # Списки ролей для ansible-galaxy
│   ├── ci-config.yml      # Маппинг vars → playbooks для CI
│   └── ...
│
├── roles/                 # Скачанные роли (gitignored)
└── library/               # mitogen после switch-to-mitogen (gitignored)
```

## Назначение ключевых каталогов

| Каталог | Назначение |
|---------|------------|
| `playbooks/` | Исполняемые плейбуки; большинство — один `run-*.yml` на одну Galaxy-роль |
| `host_vars/<hostname>/` | Файлы вида `traefik.yml`, `docker.yml` — конфиг сервиса на хосте |
| `group_vars/<group>/` | Переменные для групп из inventory |
| `inventory/hosts` | Список хостов и групп Ansible |
| `tools/roles_lists/` | YAML-списки для `ansible-galaxy install -r` |
| `vars/extra.yaml` | Подключается shebang-плейбуками (`-e @vars/extra.yaml`) |
| `daemon/` | HTTP API: запись host_vars/inventory и фоновый playbook |

## Что не в git

Из [`.gitignore`](../.gitignore):

- `roles/*` — скачиваются `./tools/get-roles.sh`
- `library` — mitogen после `ansible-playbook tools/switch-to-mitogen.yml`
- `group_vars/all.yml` — локальные секреты/переопределения
- `inventory/testing.hosts` — тестовый инвентарь

## Co-located документация

| Место | Содержание |
|-------|------------|
| `daemon/readme.md` | API, curl-примеры, алгоритмы демона |
| `host_vars/.examples/` | Готовые YAML и `monitor/readme.md` |
| `inventory/README.md` | Ссылка на guides |

См. также: [deployment-flow.md](deployment-flow.md).
