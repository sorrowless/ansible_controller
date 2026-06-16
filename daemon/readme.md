# Техническая документация: Провижининг-демон (daemon/main.py)

Скрипт `daemon/main.py` представляет собой легковесный REST API сервис, который выступает в роли "оркестратора" для локального запуска Ansible. Он преобразует входящие HTTP POST запросы в файлы конфигурации Ansible (инвентарь и переменные хостов) и инициирует асинхронный запуск сценариев развертывания.

---

## 1. Архитектура и возможности скрипта

Сервис решает три фундаментальные задачи:
1. **Валидация данных:** Принимает структурированный JSON, проверяет типы данных и обязательность полей с помощью библиотеки `Pydantic`.
2. **Управление состоянием (IaC State):** На лету модифицирует файлы конфигурации Ansible на локальной файловой системе (WSL), соблюдая идемпотентность (повторные запросы обновляют существующие данные, а не дублируют их).
3. **Асинхронность (Non-blocking):** Инициирует запуск тяжелых плейбуков в фоновом режиме, не блокируя поток веб-сервера.

---

## 2. Подробный разбор функций и алгоритмов их работы

### А. Схемы данных (Pydantic-модели)
```python
class Credentials(BaseModel)
class Metadata(BaseModel)
class DeployRequest(BaseModel)
```
* **Как работают:** Классы наследуются от `pydantic.BaseModel`. При получении запроса FastAPI автоматически парсит JSON и проверяет его структуру. Если в запросе не хватает обязательного поля (например, `ansible_password`) или передан неверный тип данных (например, вместо списка строк лейблов передано число), API мгновенно вернет ошибку `422 Unprocessable Entity`, не выполняя код дальше.

### Б. Функция `update_inventory`
```python
def update_inventory(hostname: str, ip_address: str, password: str)
```
* **Назначение:** Добавление нового хоста в группу `[test_hosts]` файла `inventory/hosts` или обновление параметров подключения, если хост уже существует [1].
* **Алгоритм работы:**
  1. Скрипт считывает весь файл `inventory/hosts` в оперативную память в виде строки.
  2. Генерируется целевая строка подключения для хоста:
     `hostname ansible_ip=ip_address ansible_ssh_common_args="..." ansible_password='password'`
  3. Используется регулярное выражение `re.compile(rf'^{hostname}\s+ansible_ip=.*$', re.MULTILINE)`:
     * **Если хост найден:** регулярное выражение заменяет всю старую строку хоста на новую (обновляя IP или пароль).
     * **Если хост не найден:** скрипт ищет строку `[test_hosts]` и вставляет новую строку сразу под ней.
     * **Если группы нет:** строка дописывается в конец файла.
  4. Файл `inventory/hosts` перезаписывается обновленной строкой.

### В. Функция `write_host_vars`
```python
def write_host_vars(hostname: str, ip_address: str, req_data: DeployRequest)
```
* **Назначение:** Формирование файлов переменных в каталоге `host_vars/<hostname>/`.
* **Алгоритм работы:**
  1. Создает каталог `host_vars/<hostname>/`, если он отсутствует, используя флаг `exist_ok=True`.
  2. Генерирует словарь (dict) системных переменных и записывает его в `host_vars/<hostname>/main.yml` в формате YAML.
  3. Генерирует словарь переменных для мониторинга и записывает его в `host_vars/<hostname>/node-exporter.yml`.
  4. При записи принудительно добавляется заголовок `---` в начало файлов, чтобы соответствовать спецификации YAML-инвентарей Ansible [1].

### Г. Функция `run_ansible_playbook` (Асинхронная)
```python
async def run_ansible_playbook(hostname: str)
```
* **Назначение:** Фоновый запуск команды `ansible-playbook` без блокировки API-сервера.
* **Алгоритм работы:**
  1. Генерирует уникальное имя лог-файла с временной меткой: `logs/<hostname>_<YYYYMMDD_HHMMSS>.log`.
  2. Формирует список аргументов командной строки для вызова Ansible:
     `ansible-playbook -i <путь_к_инвентарю> <путь_к_плейбуку> -l <hostname>`
     *Использование флага `-l` (limit) критически важно — это гарантирует, что плейбук применится только к конкретному хосту, пришедшему в запросе, даже если в группе `[test_hosts]` прописано еще 50 серверов.*
  3. Использует `asyncio.create_subprocess_exec` для старта процесса в ОС.
  4. Перенаправляет стандартный вывод (stdout) и вывод ошибок (stderr) процесса напрямую в созданный файл лога.
  5. Ждет завершения процесса (`await process.wait()`), после чего записывает в лог статус-код завершения.

### Д. Эндпоинт `/deploy`
```python
@app.post("/deploy", status_code=status.HTTP_202_ACCEPTED)
async def deploy_node_exporter(payload: DeployRequest, background_tasks: BackgroundTasks)
```
* **Назначение:** Точка входа для HTTP POST запросов.
* **Алгоритм работы:**
  1. Вызывает синхронные функции `write_host_vars` и `update_inventory` для подготовки файлов конфигурации [1]. Если на этом этапе происходит ошибка ввода-вывода (например, нет прав на запись в файл), сервис сразу вернет ошибку `500 Internal Server Error`.
  2. Если файлы подготовлены успешно, регистрирует асинхронную функцию `run_ansible_playbook` в планировщике `BackgroundTasks` FastAPI.
  3. Возвращает клиенту JSON-ответ со статусом `202 Accepted`, завершая HTTP-сессию.
  4. После этого FastAPI в фоновом режиме запускает зарегистрированную задачу деплоя.

---

## 3. Файловые операции и изменения в инфраструктуре кода

При успешном прохождении запроса на хост `m9test-vm-024` с IP `62.76.115.218`, демон вносит следующие изменения в репозиторий:

### А. Изменение файла `inventory/hosts`
**Как изменяется:** В секцию `[test_hosts]` вставляется/обновляется строка конфигурации.
**До выполнения запроса:**
```ini
[test_hosts]
```
**После выполнения запроса:**
```ini
[test_hosts]
m9test-vm-024 ansible_ip=62.76.115.218 ansible_ssh_common_args="-o PreferredAuthentications=password -o PubkeyAuthentication=no" ansible_password='секретный_пароль'
```

### Б. Создание/Перезапись файла `host_vars/m9test-vm-024/main.yml`
**Как изменяется:** Создается с нуля или перезаписывается. Содержит только общие метаданные и параметры подключения SSH.
```yaml
---
ansible_become: true
ansible_domainname: 62.76.115.218
ansible_host: '{{ ansible_domainname }}'
ansible_ip: 62.76.115.218
ansible_port: '{{ sshd_port }}'
ansible_user: root
metainfo:
  company: AKH
  placement: AKH
```

### В. Создание/Перезапись файла `host_vars/m9test-vm-024/node-exporter.yml`
**Как изменяется:** Создается с нуля или перезаписывается. Содержит переменные конфигурации роли.
```yaml
---
node_exporter_docker_labels:
- traefik.enable=true
- traefik.swarm.network=prom_network
- traefik.http.routers.xray-checker-rus.rule=Host(`rus.checker.openworld.bot`)
- traefik.http.routers.xray-checker-rus.middlewares=basic-auth@file
- traefik.http.routers.xray-checker-rus.tls=true
- traefik.http.routers.xray-checker-rus.tls.certResolver=acmeDNS
- traefik.http.services.xray-checker-rus.loadbalancer.server.port=2112
node_exporter_docker_network_name: prom_network
node_exporter_host_address: 0.0.0.0
node_exporter_run_in_docker: true
node_exporter_stack_name: node_exporter
node_exporter_swarm_cluster: false
node_exporter_version: 1.4.0
```

### Г. Создание лога в папке `logs/`
**Как изменяется:** Создается новый текстовый файл, например `logs/m9test-vm-024_20260615_162001.log`. В него в реальном времени транслируется весь стандартный поток вывода команды `ansible-playbook`.

---

## 4. Сводная таблица взаимодействия компонентов

| Компонент / Шаг | Действие | Тип операции | Влияние на систему |
| :--- | :--- | :--- | :--- |
| **API Эндпоинт** | Прием запроса | Чтение JSON (Память) | Проверка корректности структуры |
| **`write_host_vars`** | Запись YAML в `host_vars/` | Дисковая запись (I/O) | Обновляет/Создает файлы переменных хоста |
| **`update_inventory`** | Чтение и запись `inventory/hosts` | Дисковый I/O + Regex | Обновляет/Добавляет строку подключения хоста в инвентарь |
| **`run_ansible_playbook`**| Fork процесса `ansible-playbook` | Вызов системной команды | Инициирует сетевое SSH-соединение с целевой VM |
| **Фоновый логгер** | Запись вывода в `logs/*.log` | Потоковая запись | Фиксирует ход развертывания для дебага |

Ниже приведен раздел документации с примерами `curl`-команд и подробным пошаговым описанием жизненного цикла запроса. Ты можешь сразу скопировать этот текст в `README.md` твоего проекта.

---

## 5. Инструкция по вызову API (CURL) и жизненный цикл запроса

### А. Примеры CURL-команд для запуска деплоя

#### Вариант 1: Полный боевой запрос (с кастомными лейблами Traefik)
Этот запрос передает полную конфигурацию для развертывания `node_exporter` в Docker с интеграцией в Traefik:

```bash
curl -X POST http://127.0.0.1:8000/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "m9test-vm-024",
    "ip_address": "62.76.115.218",
    "credentials": {
      "ansible_user": "root",
      "ansible_password": "YOUR_ACTUAL_ROOT_PASSWORD"
    },
    "metadata": {
      "placement": "AKH",
      "company": "AKH"
    },
    "labels": [
      "traefik.enable=true",
      "traefik.swarm.network=prom_network",
      "traefik.http.routers.xray-checker-rus.rule=Host(`rus.checker.openworld.bot`)",
      "traefik.http.routers.xray-checker-rus.middlewares=basic-auth@file",
      "traefik.http.routers.xray-checker-rus.tls=true",
      "traefik.http.routers.xray-checker-rus.tls.certResolver=acmeDNS",
      "traefik.http.services.xray-checker-rus.loadbalancer.server.port=2112"
    ]
  }'
```

#### Вариант 2: Минимальный запрос (с использованием дефолтных значений)
Благодаря настройкам Pydantic-моделей, поля `ansible_user`, `placement`, `company` и `labels` имеют дефолтные значения. Их можно опустить в запросе:

```bash
curl -X POST http://127.0.0.1:8000/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "m9test-vm-024",
    "ip_address": "62.76.115.218",
    "credentials": {
      "ansible_password": "YOUR_ACTUAL_ROOT_PASSWORD"
    }
  }'
```

---

### Б. Что происходит под капотом после отправки CURL (Жизненный цикл запроса)

Процесс от нажатия клавиши `Enter` на стороне клиента до работающего контейнера на целевом сервере разделен на 5 последовательных фаз:

```
[ Клиент (CURL) ] 
       │ 1. HTTP POST (Запрос)
       ▼
┌────────────────────────────────────────────────────────┐
│ FastAPI Provisioner Daemon (WSL / Сервер управления)   │
│                                                        │
│  2. Валидация JSON (Pydantic)                          │
│  3. Генерация файлов host_vars/ и обновление hosts     │
│                                                        │
│  4. Мгновенный HTTP-ответ "202 Accepted" ──────────────┼──► [Клиент получает ответ]
│                                                        │
│  5. Регистрация Background Task (Асинхронный запуск)   │
└──────────────────────────┬─────────────────────────────┘
                           │ 6. fork процесса ansible-playbook
                           ▼
┌────────────────────────────────────────────────────────┐
│ Операционная система (WSL Kernel)                      │
│                                                        │
│  7. Запуск процесса ansible-playbook -l m9test-vm-024  │
│  8. Перенаправление stdout/stderr в logs/m9test...log  │
└──────────────────────────┬─────────────────────────────┘
                           │ 9. SSH-соединение (Порт 22)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Целевой хост (VM: 62.76.115.218)                       │
│                                                        │
│  10. Проверка условий (Docker, Сеть prom_network)      │
│  11. Запуск контейнера node_exporter с новыми лейблами  │
└────────────────────────────────────────────────────────┘
```

#### Фаза 1: Сетевое взаимодействие и валидация (время: ~5-15 мс)
1. Клиент выполняет HTTP-рукопожатие и отправляет payload на порт `8000` демона.
2. Веб-сервер `uvicorn` передает тело запроса в FastAPI.
3. FastAPI запускает Pydantic-валидатор. Если типы данных верны, запрос пропускается дальше. Если нет — клиенту возвращается статус `422` с описанием ошибки парсинга.

#### Фаза 2: Локальное изменение состояния / IaC (время: ~10-30 мс)
4. Демон выполняет синхронный метод `write_host_vars`:
   * Создает папку `host_vars/m9test-vm-024/`.
   * Перезаписывает файл `main.yml` (записывает IP, креды подключения, метадату).
   * Перезаписывает файл `node-exporter.yml` (записывает конфигурацию контейнера и его новые лейблы из запроса) [1].
5. Демон выполняет синхронный метод `update_inventory`:
   * Считывает файл `inventory/hosts`.
   * Находит секцию `[test_hosts]` и с помощью регулярного выражения вставляет или перезаписывает строку подключения для `m9test-vm-024` с актуальным IP и паролем.

#### Фаза 3: Разделение процессов и ответ клиенту (время: ~5 мс)
6. Скрипт регистрирует функцию `run_ansible_playbook` в фоновом пуле задач FastAPI (`BackgroundTasks`).
7. Демон формирует HTTP-ответ со статусом `202 Accepted` и отправляет его обратно клиенту. **На этом этапе сетевое соединение с клиентом закрывается.** Клиент свободен и может продолжать работу, в то время как деплой только начинается.

#### Фаза 4: Асинхронное выполнение Ansible (время: ~10-25 секунд)
8. FastAPI в фоновом потоке вызывает зарегистрированную задачу `run_ansible_playbook`.
9. Функция создает лог-файл в каталоге `logs/m9test-vm-024_<timestamp>.log`.
10. С помощью `asyncio.create_subprocess_exec` порождается дочерний системный процесс Linux:
    `ansible-playbook -i inventory/hosts playbooks/exporters/run-exporter-node.yml -l m9test-vm-024`
11. Стандартный вывод Ansible (stdout) и ошибки (stderr) перенаправляются напрямую в дескриптор открытого лог-файла.

#### Фаза 5: Изменение состояния на целевой VM (время выполнения Ansible)
12. Ansible подключается к удаленной виртуалке `62.76.115.218` по протоколу SSH (порт 22), используя root-пользователя и пароль из инвентаря.
13. Проверяется структура директорий на удаленной машине, раскатываются скрипты сбора метрик APT.
14. Модуль `community.docker.docker_compose_v2` генерирует временный compose-файл на удаленной машине и вызывает локальный Docker Daemon.
15. Docker Daemon видит изменения в лейблах, перезапускает контейнер `node_exporter` с новыми параметрами (наш статус `changed=1`) [1].
16. Процесс Ansible на стороне WSL успешно завершается с кодом `0`. Лог закрывается финальной строкой: `=== Finished deploy at ... with code 0 ===`.