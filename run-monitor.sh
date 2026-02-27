#!/usr/bin/env bash

./playbooks/configuration/run-server-common.yml -l $HOST
./playbooks/services/run-docker.yml -l $HOST
./playbooks/monitoring/run-vmstorage.yml -l $HOST
./playbooks/monitoring/run-vminsert.yml -l $HOST
./playbooks/monitoring/run-vmselect.yml -l $HOST
./playbooks/monitoring/run-vmagent.yml -l $HOST

./playbooks/services/run-traefik.yml -l $HOST

./playbooks/monitoring/run-vmalert.yml -l $HOST
