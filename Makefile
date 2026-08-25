.PHONY: help prepare update-from-upstream daemon sshconfig

# Основные переменные
VENV := .venv
PYTHON ?= 3.12
HOST ?=
DAEMON_HOST ?= 127.0.0.1
DAEMON_PORT ?= 8000
ANSIBLE_ARGS ?=

# Путь к docker-compose
COMPOSE := docker compose

# Поиск всех playbook'ов вида run-*.yml, исключая локальные и служебные
PLAYBOOKS := $(shell find playbooks -type f -name 'run-*.yml' \
	! -path 'playbooks/utils/run-desktop.yml' \
	! -path 'playbooks/utils/checks.yml' 2>/dev/null)

# Генерация имён целей из путей: basename без run- и .yml
TARGETS := $(foreach p,$(PLAYBOOKS),$(patsubst run-%,%,$(basename $(notdir $(p)))))

# Шаблон для динамической цели
define PLAYBOOK_RULE
.PHONY: $1
$1: prepare
	@HOST_VAL="$${HOST:-$$(bash tools/select-hosts.sh)}"; \
	if [ -z "$$HOST_VAL" ]; then echo "No host selected"; exit 1; fi; \
	echo "==> Running playbook $2 on $$HOST_VAL"; \
	$(COMPOSE) run --rm -e HOST="$$HOST_VAL" ansible ansible-playbook $2 -l "$$HOST_VAL" $(ANSIBLE_ARGS); \
	status=$$?; \
	if [ $$status -eq 0 ]; then \
		echo "==> Playbook finished, running post-checks"; \
		$(COMPOSE) run --rm -e HOST="$$HOST_VAL" ansible ansible-playbook playbooks/utils/checks.yml -l "$$HOST_VAL" $(ANSIBLE_ARGS); \
		status=$$?; \
	fi; \
	exit $$status
endef

# Генерация всех динамических целей
$(foreach p,$(PLAYBOOKS),$(eval $(call PLAYBOOK_RULE,$(patsubst run-%,%,$(basename $(notdir $(p)))),$(p))))

# Статические цели
help:
	@echo 'Targets:'
	@echo '  make prepare               - bootstrap uv, venv, poetry, and daemon deps (macOS / Ubuntu)'
	@echo '  make update-from-upstream  - update from upstream if "upstream" remote exists'
	@echo '  make sshconfig             - change ssh config on localhost'
	@echo '  make daemon                - start Ansible provisioner API (127.0.0.1:8000)'
	@echo ''
	@echo 'Dynamic playbook targets (generated from playbooks/):'
	@for t in $(sort $(TARGETS)); do \
		echo "  make $$t"; \
	done
	@echo ''
	@echo 'HOST can be one host or comma-separated: HOST=ru01.sbog.org,us03.sbog.org'
	@echo 'Without HOST, fzf prompts for host(s) from host_vars/'
	@echo 'Additional ansible arguments can be passed via ANSIBLE_ARGS'

prepare:
	@bash tools/prepare.sh "$(PYTHON)"

update-from-upstream:
	$(call git remote update && git pull --no-ff upstream master && git push origin master)

# Локальная задача (не в контейнере)
sshconfig: prepare
	@. $(VENV)/bin/activate && ./playbooks/utils/run-desktop.yml -c 'localhost,' -t sshconfig

daemon: prepare
	@. $(VENV)/bin/activate && uvicorn main:app --app-dir daemon \
		--host $(DAEMON_HOST) --port $(DAEMON_PORT)
