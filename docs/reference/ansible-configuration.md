# Конфигурация Ansible

## ansible.cfg

Корневой [`ansible.cfg`](../../ansible.cfg) — настройки по умолчанию.

| Параметр | Значение | Описание |
|----------|----------|----------|
| `inventory` | `inventory/hosts` | Путь к инвентарю |
| `roles_path` | `roles` | Каталог Galaxy-ролей |
| `vault_identity_list` | `default@tools/get-vault-pass` | Источник vault-пароля |
| `forks` | `25` | Параллелизм |
| `fact_caching` | `jsonfile` | Кэш фактов в `/tmp/ansible/facts` |
| `log_path` | `/tmp/ansible.log` | Лог Ansible |

SSH: `ControlMaster`, `pipelining`, отключена strict host key checking.

## vars/extra.yaml

Подключается shebang-плейбуками:

```yaml
ansible_become_pass: "{{ lookup('env', 'ANSIBLE_BECOME_PASS') }}"
ansible_vault_pass: "{{ lookup('env', 'ANSIBLE_VAULT_REAL_PASS') }}"
```

Перед запуском плейбуков:

```bash
. ./tools/set-vars.sh
```

## Vault

1. `set-vars.sh` экспортирует `ANSIBLE_VAULT_REAL_PASS`
2. [`tools/get-vault-pass`](../../tools/get-vault-pass) выводит его для Ansible
3. `ansible.cfg` указывает `vault_identity_list = default@tools/get-vault-pass`

Зашифрованные значения в vars используют стандартный Ansible Vault.

## Mitogen (опционально)

После `ansible-playbook tools/switch-to-mitogen.yml`:

- mitogen в `library/` (gitignored)
- `set-vars.sh` выставляет:
  - `ANSIBLE_STRATEGY_PLUGINS`
  - `ANSIBLE_STRATEGY=mitogen_linear`

## Переменные окружения (сводка)

| Переменная | Источник | Назначение |
|------------|----------|------------|
| `ANSIBLE_BECOME_PASS` | set-vars.sh | sudo/become |
| `ANSIBLE_VAULT_REAL_PASS` | set-vars.sh | vault decrypt |
| `ANSIBLE_VAULT_PASSWORD_FILE` | set-vars.sh | путь к get-vault-pass |
| `ANSIBLE_STRATEGY` | set-vars.sh | mitogen_linear |
| `ANSIBLE_STRATEGY_PLUGINS` | set-vars.sh | путь к mitogen plugins |

## vars/dotfiles_vars.yml

Дополнительные переменные для desktop/dotfile плейбуков (`utils/run-desktop.yml`).

## Локальные переопределения (gitignored)

- `group_vars/all.yml`
- `inventory/testing.hosts`

Не коммитить секреты в отслеживаемые файлы.
