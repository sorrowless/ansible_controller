# Быстрый старт

Пошаговая настройка окружения и первый деплой. Предполагается macOS или Linux с установленным Ansible.

## Требования

| Компонент | Обязательность | Установка |
|-----------|----------------|-----------|
| Ansible + ansible-galaxy | Обязательно | `pip install ansible` или пакет ОС |
| `uv` | Рекомендуется | Ставится через `make prepare` |
| `fzf` | Для интерактивного `make` | `brew install fzf` (macOS) |
| GNU readlink | Для `set-vars.sh` на macOS | `brew install coreutils` |

## 1. Клонировать и подготовить venv

```bash
cd ansible_controller_common_upstream
make prepare
```

Создаётся `.venv`, устанавливаются poetry и зависимости из `daemon/requirements.txt`.

## 2. Настроить учётные данные Ansible

```bash
. ./tools/set-vars.sh
```

Скрипт запрашивает become-пароль и vault-пароль, экспортирует переменные окружения. Если mitogen установлен в `library/`, включает стратегию `mitogen_linear`.

**Важно:** вызывать через точку (`.`), не `bash tools/set-vars.sh` — иначе переменные не попадут в текущую оболочку.

## 3. Создать инвентарь и host_vars

Скопируйте пример инвентаря и отредактируйте:

```bash
cp inventory/testing.hosts.example inventory/hosts
# отредактируйте inventory/hosts — добавьте свой хост в нужные группы
```

Создайте каталог переменных хоста по образцу:

```bash
mkdir -p host_vars/myhost.example.com
cp host_vars/.examples/idp.domain.com/traefik.yml host_vars/myhost.example.com/
# отредактируйте traefik.yml под свой хост
```

Убедитесь, что хост в inventory входит в группу `traefik` (см. `hosts:` в `playbooks/services/run-traefik.yml`).

## 4. Скачать роли

```bash
./tools/get-roles.sh traefik
```

Без аргументов скрипт попытается установить роли из **всех** файлов в `tools/roles_lists/` — это долго. Указывайте только нужные имена.

## 5. Запустить плейбук

```bash
./playbooks/services/run-traefik.yml -l myhost.example.com
```

Или через Make:

```bash
HOST=myhost.example.com make traefik
```

## 6. Проверить список хостов

```bash
./tools/nodes_list.sh
```

Таблица: hostname, IP, placement, статус SSH-конфига.

## Опционально: ускорение через mitogen

```bash
ansible-playbook tools/switch-to-mitogen.yml
. ./tools/set-vars.sh   # повторно — подхватит mitogen из library/
```

## Опционально: REST-демон

```bash
make daemon
# Swagger UI: http://127.0.0.1:8000/docs
```

Подробности — [provisioner-daemon.md](provisioner-daemon.md).

## Типичные проблемы

| Симптом | Решение |
|---------|---------|
| `ansible-galaxy not found` | Установить Ansible |
| `greadlink not found` (macOS) | `brew install coreutils` |
| Роль не найдена | `./tools/get-roles.sh <имя-файла-из-roles_lists>` |
| Vault error | Повторить `. ./tools/set-vars.sh` |
| Хост не в группе плейбука | Проверить `inventory/hosts` и `hosts:` в playbook |

## Дальше

- [configuring-hosts.md](configuring-hosts.md) — детали inventory и vars
- [traefik-deploy.md](../examples/traefik-deploy.md) — развёрнутый пример Traefik
- [minimal-server.md](../examples/minimal-server.md) — базовый стек сервера
