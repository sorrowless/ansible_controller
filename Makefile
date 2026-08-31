include tools/generated-playbooks.mk

.PHONY: help prepare daemon sshconfig update-from-upstream generate-playbooks

VENV := .venv
PYTHON ?= 3.12
HOST ?= ${HOST}
DAEMON_HOST ?= 127.0.0.1
DAEMON_PORT ?= 8000

define run_with_host
	@export HOST="$${HOST:-$$(bash tools/select-hosts.sh)}"; \
	. $(VENV)/bin/activate && $(1) -l $$HOST && \
	./playbooks/utils/run-checks.yml -l $$HOST
endef

help:
		@echo 'Targets:'
		@echo '  make daemon                - start Ansible provisioner API (127.0.0.1:8000)'
		@echo '  make prepare               - bootstrap uv, venv, poetry, and daemon deps (macOS / Ubuntu)'
		@echo '  make sshconfig             - change ssh config on localhost'
		@echo '  make update-from-upstream  - update from upstream if "upstream" remote exists'
		@echo '  make generate-playbooks    - generate Make targets for Ansible playbooks into tools/generated-playbooks.mk'
		@echo '                              existing Make targets are skipped and not added to the generated .mk file'
		@echo ''
		@echo 'HOST can be one host or comma-separated: HOST=ru01.sbog.org,us03.sbog.org'
		@echo 'Without HOST, fzf prompts for host(s) from host_vars/'


prepare:
		@bash tools/prepare.sh "$(PYTHON)"

update-from-upstream:
		$(call git remote update && git pull --no-ff upstream master && git push origin master)

daemon: prepare
		@. $(VENV)/bin/activate && uvicorn main:app --app-dir daemon \
			--host $(DAEMON_HOST) --port $(DAEMON_PORT)

sshconfig: prepare
		@. $(VENV)/bin/activate && ./playbooks/utils/run-desktop.yml -c 'localhost,' -t sshconfig

generate-playbooks:
		python3 tools/generate-make-targets.py; \

%:
		@if [ -z "$(GENERATED_ONCE)" ]; then \
				$(MAKE) GENERATED_ONCE=1 generate-playbooks; \
				$(MAKE) $@; \
		else \
				echo "Unknown target: $@" >&2; \
				exit 1; \
		fi
