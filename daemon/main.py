# daemon/main.py
import os
import re
import yaml
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Ansible Provisioner Daemon", version="1.0.0")

# Пути относительно корня проекта Ansible
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST_VARS_DIR = os.path.join(BASE_DIR, "host_vars")
INVENTORY_FILE = os.path.join(BASE_DIR, "inventory", "hosts")
PLAYBOOK_PATH = os.path.join(BASE_DIR, "playbooks", "exporters", "run-exporter-node.yml")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Создаем папку для логов, если её нет
os.makedirs(LOGS_DIR, exist_ok=True)

# Описание схем данных API (Pydantic)
class Credentials(BaseModel):
    ansible_user: str = "root"
    ansible_password: str

class Metadata(BaseModel):
    placement: str = "AKH"
    company: str = "AKH"

class DeployRequest(BaseModel):
    hostname: str = Field(..., description="Имя хоста, например, m9test-vm-024")
    ip_address: str = Field(..., description="IP адрес хоста")
    credentials: Credentials
    metadata: Metadata
    labels: List[str] = Field(default=[], description="Список лейблов для докера")

def update_inventory(hostname: str, ip_address: str, password: str):
    """
    Безопасно добавляет или обновляет хост в секции [test_hosts] файла инвентаря.
    """
    if not os.path.exists(INVENTORY_FILE):
        raise FileNotFoundError(f"Inventory file not found at: {INVENTORY_FILE}")
        
    with open(INVENTORY_FILE, "r") as f:
        content = f.read()

    # Строка, которую нужно вставить/обновить
    new_line = f'{hostname} ansible_ip={ip_address} ansible_ssh_common_args="-o PreferredAuthentications=password -o PubkeyAuthentication=no" ansible_password=\'{password}\''

    # Проверяем, есть ли уже этот хост в файле
    host_pattern = re.compile(rf'^{hostname}\s+ansible_ip=.*$', re.MULTILINE)
    
    if host_pattern.search(content):
        # Если хост есть, заменяем его строку на новую
        updated_content = host_pattern.sub(new_line, content)
    else:
        # Если хоста нет, ищем секцию [test_hosts] и вставляем под неё
        section_pattern = re.compile(r'^\[test_hosts\]$', re.MULTILINE)
        if section_pattern.search(content):
            updated_content = section_pattern.sub(f"[test_hosts]\n{new_line}", content)
        else:
            # Если даже секции нет, просто аппендим в конец
            updated_content = content + f"\n[test_hosts]\n{new_line}\n"

    with open(INVENTORY_FILE, "w") as f:
        f.write(updated_content)

def write_host_vars(hostname: str, ip_address: str, req_data: DeployRequest):
    """
    Разделяет переменные:
    - Общие настройки хоста пишет в main.yml
    - Настройки экспортера пишет в node-exporter.yml
    """
    host_dir = os.path.join(HOST_VARS_DIR, hostname)
    os.makedirs(host_dir, exist_ok=True)
    
    # 1. Запись общих настроек в main.yml
    main_file = os.path.join(host_dir, "main.yml")
    main_vars = {
        "metainfo": {
            "placement": req_data.metadata.placement,
            "company": req_data.metadata.company
        },
        "ansible_ip": ip_address,
        "ansible_domainname": ip_address,
        "ansible_host": "{{ ansible_domainname }}",
        "ansible_port": "{{ sshd_port }}",
        "ansible_user": req_data.credentials.ansible_user,
        "ansible_become": True
    }
    with open(main_file, "w") as f:
        f.write("---\n")
        yaml.safe_dump(main_vars, f, default_flow_style=False, allow_unicode=True)
        
    # 2. Запись настроек экспортера в node-exporter.yml
    exporter_file = os.path.join(host_dir, "node-exporter.yml")
    exporter_vars = {
        "node_exporter_version": "1.4.0",
        "node_exporter_run_in_docker": True,
        "node_exporter_host_address": "0.0.0.0",
        "node_exporter_stack_name": "node_exporter",
        "node_exporter_swarm_cluster": False,
        "node_exporter_docker_network_name": "prom_network",
        "node_exporter_docker_labels": req_data.labels
    }
    with open(exporter_file, "w") as f:
        f.write("---\n")
        yaml.safe_dump(exporter_vars, f, default_flow_style=False, allow_unicode=True)

async def run_ansible_playbook(hostname: str):
    """
    Запускает ansible-playbook асинхронно и пишет логи в файл.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(LOGS_DIR, f"{hostname}_{timestamp}.log")
    
    # Запускаем плейбук, ограничивая выполнение только целевым хостом через флаг -l (limit)
    cmd = [
        "ansible-playbook",
        "-i", INVENTORY_FILE,
        PLAYBOOK_PATH,
        "-l", hostname
    ]
    
    try:
        with open(log_file_path, "w") as log_file:
            log_file.write(f"=== Starting deploy at {datetime.now()} ===\n")
            log_file.write(f"Command: {' '.join(cmd)}\n\n")
            log_file.flush()
            
            # Асинхронный запуск процесса, чтобы не блокировать FastAPI event loop
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=log_file,
                stderr=log_file
            )
            
            await process.wait()
            
            log_file.write(f"\n=== Finished deploy at {datetime.now()} with code {process.returncode} ===\n")
    except Exception as e:
        with open(log_file_path, "a") as log_file:
            log_file.write(f"\nERROR DURING EXECUTION: {str(e)}\n")

@app.post("/deploy", status_code=status.HTTP_202_ACCEPTED)
async def deploy_node_exporter(payload: DeployRequest, background_tasks: BackgroundTasks):
    try:
        # 1. Записываем / обновляем host_vars
        write_host_vars(payload.hostname, payload.ip_address, payload)
        
        # 2. Обновляем файл инвентаря
        update_inventory(payload.hostname, payload.ip_address, payload.credentials.ansible_password)
        
        # 3. Добавляем запуск плейбука в фоновые задачи FastAPI
        background_tasks.add_task(run_ansible_playbook, payload.hostname)
        
        return {
            "status": "accepted",
            "message": f"Deployment started in background for host {payload.hostname}",
            "hostname": payload.hostname,
            "ip_address": payload.ip_address
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize deployment: {str(e)}"
        )
