import argparse
import sys
import logging
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetmikoAuthenticationException, NetmikoTimeoutException
from pathlib import Path
from src.cisco_switches import parse_hosts_file, parse_commands_file

# Parse the args
parser = argparse.ArgumentParser()
parser.add_argument("hosts_file", help="The hosts file containing switch IP/DNS entry")
parser.add_argument("cmd_file", help="Commands to be sent to the switch. One per line")
parser.add_argument("--username", help="Username for switch login")
parser.add_argument("--password", help="Password for switch login")
args = parser.parse_args()

if not args.hosts_file or not args.cmd_file:
    print("You must specify both a host file and command file")
    exit(1)

username = args.username if args.username else None
password = args.password if args.password else None

# Get an instance of a logger
log_file = 'results.log'
file_handler = logging.FileHandler(log_file)
stream_handler = logging.StreamHandler(sys.stdout)
file_handler.setLevel(logging.ERROR)
stream_handler.setLevel(logging.ERROR)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


# the files
hosts_path = Path() / args.hosts_file
cmd_path = Path() / args.cmd_file

# open and read files, and handle errors if necessary
try:
    with hosts_path.open() as file:
        hosts = parse_hosts_file(file, username, password)
except (FileExistsError, FileNotFoundError):
    logger.error(f"Hosts file {hosts_path.name} not found or failed to open")
    exit(1)

try:
    with cmd_path.open() as file:
        cmds = parse_commands_file(file)
except (FileExistsError, FileNotFoundError):
    logger.error(f"Commands file {cmd_path.name} not found or failed to open")
    exit(1)

# loop over all hosts and execute necessary commands
for host in hosts:
    try:
        connection = ConnectHandler(**host)
        output = connection.send_config_set(cmds)
    except NetmikoAuthenticationException:
        logger.error(f"Auth error exception as {host['host']}")
    except NetmikoTimeoutException:
        logger.error(f"Timeout error exception {host['host']}")
    logger.debug(f"{host['host']} configured successfully")
