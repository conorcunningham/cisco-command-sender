import argparse
from netmiko import ConnectHandler
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


# the files
hosts_path = Path() / args.hosts_file
cmd_path = Path() / args.cmd_file

# open and read files, and handle errors if necessary
try:
    with hosts_path.open() as file:
        hosts = parse_hosts_file(file, username, password)
except (FileExistsError, FileNotFoundError):
    print(f"Hosts file {hosts_path.name} not found or failed to open")
    exit(1)

try:
    with cmd_path.open() as file:
        cmds = parse_commands_file(file)
except (FileExistsError, FileNotFoundError):
    print(f"Commands file {cmd_path.name} not found or failed to open")
    exit(1)

# loop over all hosts and execute necessary commands
for host in hosts:
    connection = ConnectHandler(**host)
    output = connection.send_config_set(cmds)
    print(output)
