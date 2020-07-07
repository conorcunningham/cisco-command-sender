# Cisco Command Sender
A simple tool to send commands to a list of Cisco IOS devices.

### Usage
The tool takes two arguments:
1. A file with IP addresses/hostnames. One per line
2. A file with commands to be sent to the devices. Again, one per line.

Run the tool as follows:
```bash
python command_sender.py [-h] [--username USERNAME] [--password PASSWORD] hosts_file cmd_file
```
As an example
```bash
$ python command_sender.py ./data_files/hosts.txt ./data_files/commands.txt
```

### Example Hosts File
```text
192.168.2.2
myrouter.mydomain.com
10.10.12.1
```
### Example Commands File
**N.B.** Commands are sent to the configuration prompt, so if a show command is to be executed, then 'do' must be prepended to the command
```text
do show ip int br
vlan 987
name monkey
exit
do show vlan
```