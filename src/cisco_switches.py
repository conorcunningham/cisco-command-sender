# from netmiko import ConnectHandler


class CiscoCommandSender:
    """
    A straightforward class which takes a formatted text file
    defining devices which must be configured with a command.
    Give the class a command to be sent to the cisco devices
    and it will attempt to send the command to all devics in the
    text file
    """
    def __init__(self, hosts_file):
        self.hosts_file = hosts_file

    def read_hosts_file(self):
        pass


def parse_hosts_file(file, username, password, device_type='cisco_ios'):
    hosts_array = []
    for line in file:
        host = {
            'device_type': device_type,
            'host': line.strip(),
            'username': username,
            'password': password,
        }
        hosts_array.append(host)
    return hosts_array


def parse_commands_file(file):
    return [line.strip() for line in file]


def analyse_output_key_value(output, key, value):
    for line in output.split("\n"):
        if key in line:
            return True if value in line else False
    return False
