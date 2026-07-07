.PHONY: help prepare daemon sshconfig docker-services traefik iptables

VENV := .venv
PYTHON ?= 3.12
HOST ?= ${HOST}
DAEMON_HOST ?= 127.0.0.1
DAEMON_PORT ?= 8000

define run_with_host
	@export HOST="$${HOST:-$$(bash tools/select-hosts.sh)}"; \
	. $(VENV)/bin/activate && $(1) -l $$HOST
endef

help:
		@echo 'Targets:'
		@echo '  make prepare               - bootstrap uv, venv, poetry, and daemon deps (macOS / Ubuntu)'
		@echo '  make daemon                - start Ansible provisioner API (127.0.0.1:8000)'
		@echo '  make sshconfig             - change ssh config on localhost'
		@echo '  make docker-services       - deploy docker-services (HOST or fzf)'
		@echo '  make traefik               - deploy traefik with its config (HOST or fzf)'
		@echo ''
		@echo 'HOST can be one host or comma-separated: HOST=ru01.sbog.org,us03.sbog.org'
		@echo 'Without HOST, fzf prompts for host(s) from host_vars/'

prepare:
		@bash tools/prepare.sh "$(PYTHON)"

daemon: prepare
		@. $(VENV)/bin/activate && uvicorn main:app --app-dir daemon \
			--host $(DAEMON_HOST) --port $(DAEMON_PORT)

sshconfig: prepare
		@. $(VENV)/bin/activate && ./playbooks/utils/run-desktop.yml -c 'localhost,' -t sshconfig

docker-services: prepare
		$(call run_with_host,./playbooks/services/run-docker-services.yml)

traefik: prepare
		$(call run_with_host,./playbooks/services/run-traefik.yml)

iptables: prepare
		$(call run_with_host,./playbooks/configurations/run-iptables.yml)
