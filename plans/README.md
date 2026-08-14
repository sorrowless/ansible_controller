# Планы работ

Каталог для планов изменений в репозитории Ansible Controller. Планы для компонента `daemon/` по-прежнему лежат в [`daemon/plans/`](../daemon/plans/).

## Именование файлов

```
YYYYMMDDNN-kebab-case-slug.md
```

- `YYYYMMDD` — дата создания плана
- `NN` — порядковый номер за день (`01`, `02`, …)
- `kebab-case-slug` — краткое описание задачи

Пример: `2026061701-refactor-daemon-main-py.md`

## YAML frontmatter

```yaml
---
name: Краткое название
overview: "Одно предложение о цели"
status: draft | in_progress | completed | cancelled
todos:
  - id: unique-id
    content: Описание шага
    status: pending | in_progress | completed
---
```

## Структура тела

1. **Цель** — что делаем и что сознательно не трогаем
2. **Изменения** — конкретные правки по файлам/модулям
3. **Верификация** — команды и проверки после выполнения
4. **Затронутые файлы** — таблица с относительными ссылками

## Связь с документацией

- Подробная техдока компонентов — в `docs/` и co-located readme (`daemon/readme.md` и т.п.)
- План не дублирует длинные описания API; в коде — ссылка на readme, не наоборот
