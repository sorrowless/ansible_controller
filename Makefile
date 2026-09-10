include tools/generated-playbooks.mk

.DEFAULT_GOAL := select
.PHONY: help prepare daemon sshconfig update-from-upstream generate-playbooks select import-infra-to-sshconfig

VENV := .venv
PYTHON ?= 3.12
HOST ?= ${HOST}
TAGS ?= ${TAGS}
DAEMON_HOST ?= 127.0.0.1
DAEMON_PORT ?= 8000

define run_with_host
	@if [ -z "$${HOST:-}" ]; then \
		HOST=$$(bash tools/select-hosts.sh $(1)) || exit 1; \
	fi; \
	export HOST; \
	if [ -z "$${TAGS:-}" ]; then \
		TAGS=$$(bash tools/select-tags.sh $(1)) || exit 1; \
	fi; \
	export TAGS; \
	echo " "; \
	echo ">>>> running the command below <<<<"; \
	echo "$(1) -l $$HOST -t $$TAGS"; \
	echo " "; \
	. $(VENV)/bin/activate && $(1) -l $$HOST -t $$TAGS && \
	./playbooks/utils/run-checks.yml -l "$$HOST"
endef

help:
		@echo 'Targets:'
		@echo '  make                						- Launching dynamic selection of playbooks, target hosts, and tags.
		@echo '  make daemon                		- start Ansible provisioner API (127.0.0.1:8000)'
		@echo '  make prepare               		- bootstrap uv, venv, poetry, and daemon deps (macOS / Ubuntu)'
		@echo '  make sshconfig             		- change ssh config on localhost'
		@echo '  make update-from-upstream  		- update from upstream if "upstream" remote exists'
		@echo '  make generate-playbooks    		- generate Make targets for Ansible playbooks into tools/generated-playbooks.mk'
		@echo '                              			existing Make targets are skipped and not added to the generated .mk file'
		@echo '  make import-infra-to-sshconfig - import hosts from current ansible controller to ~/.ssh/confgig
		@echo ''
		@echo 'HOST can be one host or comma-separated: HOST=ru01.sbog.org,us03.sbog.org'
		@echo 'Without HOST, fzf prompts for host(s) from host_vars/'
		@echo 'TAGS can be one tag or comma-separated: TAGS=users,iptables'
		@echo 'Without HOST, fzf prompts for host(s) from host_vars/'
		@echo 'Run "make" without arguments to interactively select a playbook via fzf (single selection).'
		@echo 'Then fzf prompts for hosts and tags: Tab = multi-select, Esc = use "all".'
		@echo 'Alternatively, set HOST=host1,host2 and TAGS=tag1,tag2 directly.'

prepare:
		@bash tools/prepare.sh "$(PYTHON)"

update-from-upstream:
		$(call git remote update && git pull --no-ff upstream master && git push origin master)

daemon: prepare
		@. $(VENV)/bin/activate && uvicorn main:app --app-dir daemon \
			--host $(DAEMON_HOST) --port $(DAEMON_PORT)

sshconfig: prepare
		@. $(VENV)/bin/activate && ./playbooks/utils/run-desktop.yml -c 'localhost,' -t sshconfig

select:
	@command -v fzf >/dev/null 2>&1 || { echo "fzf is required (brew install fzf)"; exit 1; }
	@target=$$(grep -hE '^[a-zA-Z0-9_-]+:' $(MAKEFILE_LIST) | cut -d: -f1 | sort -u | fzf --height=40% --reverse --prompt='Make target> '); \
	if [ -n "$$target" ]; then \
		$(MAKE) $$target; \
	fi

generate-playbooks:
		python3 tools/generate-make-targets.py; \

import-infra-to-sshconfig:
		python3 tools/import_infra_to_sshconf.py; \

%:
		@if [ -z "$(GENERATED_ONCE)" ]; then \
				$(MAKE) GENERATED_ONCE=1 generate-playbooks; \
				$(MAKE) GENERATED_ONCE=1 $@; \
		else \
				echo "Unknown target: $@" >&2; \
				exit 1; \
		fi
