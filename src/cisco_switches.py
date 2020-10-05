from collections import namedtuple, OrderedDict


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


def analyse_output_key_value(text_input, key, value):
    for line in text_input.split("\n"):
        if key in line:
            return True if value in line else False
    return False


def validate(output, config_to_check, confirmation_string):
    return analyse_output_key_value(output, config_to_check, confirmation_string)


def line_parser(data, search_term="DYNAMIC", delimter="\n"):
    lines = data.split(delimter)
    relevant_lines = [line for line in lines if search_term in line]
    return [line.split() for line in relevant_lines]


def strip_mac_address(mac):
    mac_separators = ":.-_"
    output = mac
    for char in mac_separators:
        output = output.replace(char, "")
    return output.upper()


def parse_mac_line_data(line):

    mac = line[0]
    vendor = " ".join(line[1:])
    return mac, vendor


def read_and_parse_mac_vendor_file(file):
    """
    Read a list of mac addresses (6 most significant HEX digits)
    Build a list with the MAC as lookup key and vendor as value
    return: Dict as described above
    """
    vendor_dict = {}
    with open(file, 'r') as vendor_file:
        for line in vendor_file:
            mac, vendor = parse_mac_line_data(line.split())
            vendor_dict[mac.upper()] = vendor
    return vendor_dict


def find_mac_vendor(mac, vendor_dict):
    mac_key = strip_mac_address(mac)[:6]
    try:
        return vendor_dict[mac_key]
    except KeyError:
        return "MAC not found in Vendor DB"


def sort_by_mac(data, mac_idx=1, port_idx=3):
    mac_addresses = {}
    for line in data:
        mac_addresses[line[mac_idx]] = line[port_idx]
    return mac_addresses


def count_mac_address_by_port(data, port_idx=3):
    mac_count = {}
    for line in data:
        mac_count[line[port_idx]] = mac_count.get(line[port_idx], 0) + 1
    return mac_count


def parse_mac_and_arp_data(data, ip_idx=1, mac_idx=3):
    ip_data = {}
    for line in data:
        ip_data[line[mac_idx]] = line[ip_idx]
    return ip_data


def map_hosts_to_ip(macs, ip, vendors):
    host_detail = namedtuple("host", "ip, mac, port, vendor")
    host_data = {}

    for mac, port in macs.items():
        mac_addr = mac
        port = port
        vendor = find_mac_vendor(mac_addr, vendors)
        ip_addr = ip.get(mac, None)
        host = host_detail(ip_addr, mac_addr, port, vendor)
        host_data[mac_addr] = host
    return host_data


def sort_and_order_data(port_data, host_data):
    port_dict = {}
    for port in port_data:
        port_dict[port[0]] = []

    for key, value in host_data.items():
        port_dict[value.port].append(value)

    ports = OrderedDict(sorted(port_dict.items(), key=lambda t: len(t[1]), reverse=True))

    return ports
