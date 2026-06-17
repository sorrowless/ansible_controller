"""Ansible provisioner REST API. See daemon/readme.md for architecture and usage."""

import asyncio
import os
import re
from datetime import datetime
from typing import List

import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST_VARS_DIR = os.path.join(BASE_DIR, "host_vars")
INVENTORY_FILE = os.path.join(BASE_DIR, "inventory", "hosts")
INVENTORY_GROUP = "test_hosts"
PLAYBOOK_PATH = os.path.join(BASE_DIR, "playbooks", "exporters", "run-exporter-node.yml")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOGS_DIR, exist_ok=True)

app = FastAPI(title="Ansible Provisioner Daemon", version="1.0.0")


class Credentials(BaseModel):
    ansible_user: str = "root"
    ansible_password: str


class Metadata(BaseModel):
    placement: str = "AKH"
    company: str = "AKH"


class DeployRequest(BaseModel):
    hostname: str = Field(..., description="Host name, e.g. m9test-vm-024")
    ip_address: str = Field(..., description="Host IP address")
    credentials: Credentials
    metadata: Metadata
    labels: List[str] = Field(default=[], description="Docker labels for node_exporter")


def _write_yaml(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n")
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)


def update_inventory(hostname: str, ip_address: str, password: str) -> None:
    """Idempotently add or update a host in the [test_hosts] inventory group."""
    if not os.path.exists(INVENTORY_FILE):
        raise FileNotFoundError(f"Inventory file not found at: {INVENTORY_FILE}")

    with open(INVENTORY_FILE, encoding="utf-8") as f:
        content = f.read()

    new_line = (
        f"{hostname} ansible_ip={ip_address} "
        'ansible_ssh_common_args="-o PreferredAuthentications=password -o PubkeyAuthentication=no" '
        f"ansible_password='{password}'"
    )
    host_pattern = re.compile(rf"^{hostname}\s+ansible_ip=.*$", re.MULTILINE)

    if host_pattern.search(content):
        updated_content = host_pattern.sub(new_line, content)
    else:
        section_header = f"[{INVENTORY_GROUP}]"
        section_pattern = re.compile(rf"^\[{INVENTORY_GROUP}\]$", re.MULTILINE)
        if section_pattern.search(content):
            updated_content = section_pattern.sub(f"{section_header}\n{new_line}", content)
        else:
            updated_content = content + f"\n{section_header}\n{new_line}\n"

    with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
        f.write(updated_content)


def write_host_vars(hostname: str, ip_address: str, req_data: DeployRequest) -> None:
    host_dir = os.path.join(HOST_VARS_DIR, hostname)
    os.makedirs(host_dir, exist_ok=True)

    _write_yaml(
        os.path.join(host_dir, "main.yml"),
        {
            "metainfo": {
                "placement": req_data.metadata.placement,
                "company": req_data.metadata.company,
            },
            "ansible_ip": ip_address,
            "ansible_domainname": ip_address,
            "ansible_host": "{{ ansible_domainname }}",
            "ansible_port": "{{ sshd_port }}",
            "ansible_user": req_data.credentials.ansible_user,
            "ansible_become": True,
        },
    )

    _write_yaml(
        os.path.join(host_dir, "node-exporter.yml"),
        {
            "node_exporter_version": "1.4.0",
            "node_exporter_run_in_docker": True,
            "node_exporter_host_address": "0.0.0.0",
            "node_exporter_stack_name": "node_exporter",
            "node_exporter_swarm_cluster": False,
            "node_exporter_docker_network_name": "prom_network",
            "node_exporter_docker_labels": req_data.labels,
        },
    )


async def run_ansible_playbook(hostname: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(LOGS_DIR, f"{hostname}_{timestamp}.log")
    cmd = [
        "ansible-playbook",
        "-i",
        INVENTORY_FILE,
        PLAYBOOK_PATH,
        "-l",
        hostname,
    ]

    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"=== Starting deploy at {datetime.now()} ===\n")
            log_file.write(f"Command: {' '.join(cmd)}\n\n")
            log_file.flush()

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=log_file,
                stderr=log_file,
            )

            await process.wait()

            log_file.write(
                f"\n=== Finished deploy at {datetime.now()} with code {process.returncode} ===\n"
            )
    except OSError as e:
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\nERROR DURING EXECUTION: {e}\n")


@app.post("/deploy", status_code=status.HTTP_202_ACCEPTED)
async def deploy_node_exporter(
    payload: DeployRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    try:
        write_host_vars(payload.hostname, payload.ip_address, payload)
        update_inventory(
            payload.hostname,
            payload.ip_address,
            payload.credentials.ansible_password,
        )
    except (OSError, FileNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize deployment: {e}",
        ) from e

    background_tasks.add_task(run_ansible_playbook, payload.hostname)

    return {
        "status": "accepted",
        "message": f"Deployment started in background for host {payload.hostname}",
        "hostname": payload.hostname,
        "ip_address": payload.ip_address,
    }
