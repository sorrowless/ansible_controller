#!python3
# Этот скрипт проходится по всем хостам в host_vars и импортирует инфраструктуру контроллера в ~/.ssh/config
# Для того чтобы узнать подробности используйте ./tools/import_infra_to_sshconf.py --help
# При запуске скрипта его опции сохрянятся в ssh config файл
# Эти сохраненные опции будут использованы при следующих запусках скрипта
# При следующем запуске скрипта, указанные опции перезапишут старые


from argparse import ArgumentParser
import os
import yaml


ARGS = None


def parse_arguments():
  parser = ArgumentParser()  
  parser.add_argument("-u", "--user",
    default = None, 
    help = "ssh-user what will be used for all hosts. Deployer by default." 
  )
  parser.add_argument("-i", "--identity",
    default = None,
    help = "Path to private ssh-key. ~/.ssh/id_rsa by default"
  )
  parser.add_argument("-p", "--port",
    default=None,
    help = "ssh port what will be used for all hosts. 22 by default." 
  )
  parser.add_argument("--ignore_options",
    default=[],
    metavar="OPTION_A,OPTION_Z",
    help = "Fields that will not be added to ssh config",
    nargs = "+"
  )
  parser.add_argument("--ignore_directories",
    default=[".DEPRECATED", ".examples"],
    metavar="DIRNAME_A,DIRNAME_Z",
    help = "Ignored directories in host_vars"
  )
  parser.add_argument("--host_prefix",
    default="",
    help = "Prefix for hosts"
  )

  global ARGS
  ARGS = vars(parser.parse_args())
  ARGS["default_user"] = "deployer"
  ARGS["default_identity"] = os.path.expanduser('~') + "/.ssh/id_rsa"
  ARGS["default_port"] = 22


def strip_ssh_conf(conf_path: str, controller_name: str):
  global ARGS
  stripped_conf_before = []
  stripped_conf_after = []
  stripped_lines = False
  host_conf_was_cat_out = False
  for line in open(conf_path, "r").read().split("\n"):
    if line[:9] == "#ac_start" and controller_name in line:
      stripped_lines = True

    if not stripped_lines and not host_conf_was_cat_out:
      stripped_conf_before.append(line)

    if not stripped_lines and host_conf_was_cat_out:
      stripped_conf_after.append(line)

    if line[:7] == "#ac_end":
      stripped_lines = False
      host_conf_was_cat_out = True

    if stripped_lines:
      if line[:10] == "#ac_config":
        directive, value = line[11:].split("=")
        if directive == "ignore_options" and len(ARGS[directive]) == 0:
          ARGS[directive] = value
        elif ARGS[directive] is None:
          ARGS[directive] = value

  return stripped_conf_before, stripped_conf_after


def yml_load_ansible_confs(path: str):
  hosts_confs = {}

  for dir in os.listdir(path):
    if dir in ARGS["ignore_directories"]: 
      continue
    host_dir = ARGS["host_prefix"] + dir
    hosts_confs[host_dir] = {}
    for file in os.listdir(path + "/" + dir):
      try:
        loaded_conf = yaml.safe_load(open(path + "/" + dir + "/" + file, "r").read())
        if isinstance(loaded_conf, str):
          continue
      except:
        continue
      
      hostname = loaded_conf.get("ansible_host", None) if "ansible_host" in loaded_conf else hosts_confs[host_dir].get("Hostname", None) 
      port = loaded_conf.get("sshd_port", None) if "sshd_port" in loaded_conf else hosts_confs[host_dir].get("Port", None) 
      user = loaded_conf.get("ansible_user", None) if "ansible_user" in loaded_conf else hosts_confs[host_dir].get("User", None) 
      identity_file = loaded_conf.get("ansible_ssh_private_key_file", None) if "ansible_ssh_private_key_file" in loaded_conf else hosts_confs[host_dir].get("IdentityFile", None) 

      hosts_confs[host_dir] = {
        "Hostname": hostname,
        "Port": port if ARGS["port"] is None else int(ARGS["port"]),
        "User": user if ARGS["user"] is None else ARGS["user"],
        "IdentityFile": identity_file if ARGS["identity"] is None else ARGS["identity"],
      }
    
    if hosts_confs[host_dir]["User"] is None:
      hosts_confs[host_dir]["User"] = ARGS["default_user"]
    if hosts_confs[host_dir]["Port"] is None:
      hosts_confs[host_dir]["Port"] = int(ARGS["default_port"])
    if hosts_confs[host_dir]["IdentityFile"] is None:
      hosts_confs[host_dir]["IdentityFile"] = ARGS["default_identity"]
    if hosts_confs[host_dir]["Hostname"] is None:
      print("Warning!!! Hostname for host ", host_dir, " not found")

    for conf in hosts_confs[host_dir].copy():
      if conf in ARGS["ignore_options"]:
        hosts_confs[host_dir].pop(conf)

  return hosts_confs


def convert_dict_to_sshconf(conf: dict, controller_name: str):
  global ARGS
  result = []

  result.append("#ac_start " + controller_name)

  for arg in ARGS:
    if arg == "ignore_options" and len(ARGS[arg]) == 0:
      result.append("#ac_config " + arg + "=" + str(ARGS[arg]))
      continue
    if "default" not in arg and ARGS[arg] is not None and arg != "save":
      result.append("#ac_config " + arg + "=" + str(ARGS[arg]))

  for host in conf:
    line = "\nHost " + host
    result.append(line)
    for directive in conf[host]:
      line = "  " + directive + " " + str(conf[host][directive])
      result.append(line)

  result.append("\n#ac_end ")

  return result


def write_config(config_path: str, config: list):
  with open(config_path, "w") as ssh_config:
    for line in config:
      if line == "":
        continue
      ssh_config.write(line + "\n")


parse_arguments()
path = os.getcwd()

controller_name = path.split("/")[-1]
conf_path = os.path.expanduser('~') + "/.ssh/config"
stripped_config_before, stripped_config_after = strip_ssh_conf(conf_path, controller_name)

ansible_conf = yml_load_ansible_confs(path+"/host_vars")
ansible_conf = convert_dict_to_sshconf(ansible_conf, controller_name)

result_conf = []
result_conf.extend(stripped_config_before)
result_conf.extend(ansible_conf)
result_conf.extend(stripped_config_after)
write_config(conf_path, result_conf)
