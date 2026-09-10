# CI-автоматизация

Скрипт [`tools/ci-script.py`](../../tools/ci-script.py) анализирует git diff относительно целевой ветки, определяет затронутые `host_vars/` и `group_vars/`, скачивает нужные роли и генерирует команды `ansible-playbook`.

Маппинг «файл переменных → плейбук» задаётся в [`tools/ci-config.yml`](../../tools/ci-config.yml).

## ci-config.yml

Формат:

```yaml
default_priority: 1000

mappings:
  docker.yml:
    playbooks/services/run-docker.yml:
      priority: 30

  server-common.yml:
    playbooks/configuration/run-pwpolicy.yml:
      priority: 40
    playbooks/configuration/run-server-common.yml:
      priority: 50
    # ...
```

- Ключ в `mappings` — имя файла vars (поддерживаются wildcards, например `scrape_configs_*.yml`)
- Значение — плейбук(и) с опциональными `priority` и `tags`
- Меньший `priority` выполняется раньше

## Режимы ci-script.py

### Автоматический (по git diff)

Просмотр команд без выполнения:

```bash
python tools/ci-script.py --preview --target_branch main
```

Выполнение:

```bash
python tools/ci-script.py --apply --target_branch main
```

Скрипт:

1. Сравнивает текущую ветку с `--target_branch`
2. Находит изменённые файлы в `host_vars/` и `group_vars/`
3. Сопоставляет с `ci-config.yml`
4. Определяет `tools/roles_lists/*.yml` по именам vars-файлов
5. Запускает `ansible-galaxy install` и сгенерированные playbook-команды

### Ручной режим

Просмотр:

```bash
python tools/ci-script.py --preview-manual "playbooks/services/run-traefik.yml -l myhost -t traefik"
```

Применение:

```bash
python tools/ci-script.py --apply-manual "playbooks/services/run-traefik.yml -l myhost -t traefik"
```

Несколько команд — через перевод строки в одном аргументе.

## Зависимости

CI-скрипт требует пакеты из [`tools/requirements.txt`](../../tools/requirements.txt) (`PyYAML`, `GitPython`, `ansible` и др.). Системный `python3` без venv их не содержит.

```bash
make prepare
. .venv/bin/activate
pip install -r tools/requirements.txt
python tools/ci-script.py --preview --target_branch main
```

## GitLab CI

В корневом README и исторически секция называлась «Gitlab-CI» — логика та же: diff vars → roles → ansible. Конкретный `.gitlab-ci.yml` в репозитории может отсутствовать; скрипт вызывается из pipeline вручную или через job.

## Связанные файлы

| Файл | Роль |
|------|------|
| `tools/ci-config.yml` | Маппинг vars → playbooks |
| `tools/roles_lists/` | Списки ролей для galaxy |
| `tools/get-roles.sh` | Тот же механизм установки ролей |

См. [roles-lists.md](../reference/roles-lists.md).
