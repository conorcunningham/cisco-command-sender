import sys
import logging
import argparse
import concurrent.futures
from pathlib import Path
from collections import Counter
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetmikoAuthenticationException, NetmikoTimeoutException
import src.cisco_switches as sw
from src.excel_processor import ExcelProcessor

# from datetime import datetime
# startTime = datetime.now()

# Parse the args
parser = argparse.ArgumentParser()
parser.add_argument("hosts_file", help="The hosts file containing switch IP/DNS entry")
parser.add_argument("cmd_file", help="Commands to be sent to the switch. One per line")
parser.add_argument("--username", help="Username for switch login")
parser.add_argument("--password", help="Password for switch login")
parser.add_argument("--threshold", help="Threshold defining how many MACs on a port make it worth investigating")
parser.add_argument("--log-file", help="Log file")
args = parser.parse_args()

if not args.hosts_file or not args.cmd_file:
    print("You must specify both a host file and command file")
    exit(1)

username = args.username if args.username else None
password = args.password if args.password else None
threshold = args.threshold if args.threshold else 1

mac_command = "show mac address-table"
arp_command = "show ip arp vlan 200"
hostname_command = "show run | i hostname"

# Build the logger
log_file = args.log_file if args.log_file else 'results.log'

file_handler = logging.FileHandler(log_file)
stream_handler = logging.StreamHandler(sys.stdout)
file_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.DEBUG)
# formatting for loggers
# file_handler_format = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
file_handler_format = logging.Formatter('%(message)s')
stream_handler_format = logging.Formatter('%(message)s')
file_handler.setFormatter(file_handler_format)
stream_handler.setFormatter(stream_handler_format)

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


# the files
hosts_path = Path() / args.hosts_file
cmd_path = Path() / args.cmd_file
data_files_dir = "data_files"
vendor_mac_file = "vendor-mac-data.txt"
vendor_mac = Path() / data_files_dir / vendor_mac_file


def main():
    logger.debug("Starting switch scan")
    # open and read files, and handle errors if necessary
    try:
        excel = ExcelProcessor("data_files/Switchfinder_poc.xlsx", username, password)
        hosts = excel.run_sheet_read()
        # with hosts_path.open() as file:
        #     hosts = sw.parse_hosts_file(file, username, password)
    except (FileExistsError, FileNotFoundError):
        logger.error(f"Hosts file {hosts_path.name} not found or failed to open")
        return

    # try:
    #     with cmd_path.open() as file:
    #         cmds = sw.parse_commands_file(file)
    # except (FileExistsError, FileNotFoundError):
    #     logger.error(f"Commands file {cmd_path.name} not found or failed to open")
    #     exit(1)

    mac_vendors = sw.read_and_parse_mac_vendor_file(vendor_mac)
    # Here we are using threading, as we are I/O bound.
    # Netmiko and Paramiko are blocking, so asyncio not possible
    # On an asyncio note, asyncssh package looks interesting
    # loop over all hosts and execute necessary commands
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for host in hosts:
            # run_ssh_connection(host, mac_vendors)
            executor.submit(run_ssh_connection, host, mac_vendors)

    # print script execution duration
    # print(datetime.now() - startTime)


def run_ssh_connection(host, mac_vendors):
    """
    Connect to the host and execute the list of commands
    Log results
    :param host: DNS or IP address of a host
    :param mac_vendors: dict of macs and vendors
    :return: None
    """
    try:
        connection = ConnectHandler(**host)
        mac_address_ouput = connection.send_command(mac_command)
        arp_output = connection.send_command(arp_command)
        hostname = connection.send_command(hostname_command).split()[1]
    except NetmikoAuthenticationException:
        logger.error(f"Auth error exception as {host['host']}")
        return 1
    except NetmikoTimeoutException:
        logger.error(f"Timeout error exception {host['host']}")
        return 1

    # determine whether the results are as expected, and log
    if mac_address_ouput is not None:
        data = sw.line_parser(mac_address_ouput)
        mac_addresses = sw.sort_by_mac(data)
        port_count = sw.count_mac_address_by_port(data)
        ordered_ports = Counter(port_count).most_common()

        if arp_output is not None:
            data = sw.line_parser(arp_output, search_term="Internet")
            ip_information = sw.parse_mac_and_arp_data(data)
            host_data = sw.map_hosts_to_ip(mac_addresses, ip_information, mac_vendors)
            ordered_data = sw.sort_and_order_data(ordered_ports, host_data)
            parse_and_display_output(ordered_data, hostname)


def parse_and_display_output(ordered_data, hostname):
    for port_data, value in ordered_data.items():
        if len(value) > threshold:
            txt = f"{hostname} Port: {port_data}"
            print(txt)
            logger.info(txt)
            for host_info in value:
                txt = f"\tMAC: {host_info.mac} \tIP: {host_info.ip} \tVendor: {host_info.vendor} # "
                print(txt)
                logger.info(txt)


if __name__ == '__main__':
    main()
