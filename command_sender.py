import sys
import logging
import argparse
import concurrent.futures
from pathlib import Path
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetmikoAuthenticationException, NetmikoTimeoutException
from src.cisco_switches import parse_commands_file, check_string_not_present
from src.excel_processor import ExcelProcessor

# from datetime import datetime
# startTime = datetime.now()

# Parse the args
parser = argparse.ArgumentParser()
parser.add_argument("hosts_file", help="The hosts file containing switch IP/DNS entry")
parser.add_argument("cmd_file", help="Commands to be sent to the switch. One per line")
parser.add_argument("--sheet", help="The Excel sheet name to be processed. Default is Sheet 1")
parser.add_argument("--username", help="Username for switch login")
parser.add_argument("--password", help="Password for switch login")
parser.add_argument("--log-file", help="Log file")
args = parser.parse_args()

if not args.hosts_file or not args.cmd_file:
    print("You must specify both a host file and command file")
    exit(1)

username = args.username if args.username else None
password = args.password if args.password else None
sheet = args.sheet if args.sheet else "Sheet 1"
print(f"Using default sheet name: {sheet}")

# Build the logger
log_file = args.log_file if args.log_file else 'results.log'
file_handler = logging.FileHandler(log_file)
stream_handler = logging.StreamHandler(sys.stdout)
file_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.ERROR)
# formatting for loggers
file_handler_format = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
stream_handler_format = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
file_handler.setFormatter(file_handler_format)
stream_handler.setFormatter(stream_handler_format)

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


# the files
hosts_path = Path() / args.hosts_file
cmd_path = Path() / args.cmd_file

# what we are checking for
# effectively we want to confirm wether some string in present in another string
# for example, by looking at the output of 'show spanning-tree summary'
# we want to confirm whether 'Loopguard Default' is enabled or disabled.
config_to_check = "Loopguard Default"
confirmation_string = "is disabled"
check_does_not_contain = "Loop guard"


def main():
    # open and read files, and handle errors if necessary
    try:
        excel = ExcelProcessor(hosts_path, sheet, username, password, ignore_status=False)
        hosts = excel.run_sheet_read()
    except (FileExistsError, FileNotFoundError):
        logger.error(f"Hosts file {hosts_path.name} not found or failed to open")
        return

    # this is for reading from a text file containing hosts
    # try:
    #     with hosts_path.open() as file:
    #         hosts = parse_hosts_file(file, username, password)
    # except (FileExistsError, FileNotFoundError):
    #     logger.error(f"Hosts file {hosts_path.name} not found or failed to open")
    #     exit(1)

    try:
        with cmd_path.open() as file:
            cmds = parse_commands_file(file)
    except (FileExistsError, FileNotFoundError):
        logger.error(f"Commands file {cmd_path.name} not found or failed to open")
        exit(1)

    # Here we are using threading, as we are I/O bound.
    # Netmiko and Paramiko are blocking, so asyncio not possible
    # On an asyncio note, asyncssh package looks interesting
    # loop over all hosts and execute necessary commands
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for host in hosts:
            # run_ssh_connection(host, cmds, excel)
            executor.submit(run_ssh_connection, host, cmds, excel)

    # save excel file to disk
    excel.append_df_to_excel(truncate_sheet=True, index=False, startrow=0)

    # print script execution duration
    # print(datetime.now() - startTime)


def run_ssh_connection(host, cmds, excel: ExcelProcessor):
    """
    Connect to the host and execute the list of commands
    Log results
    :param host: DNS or IP address of a host
    :param cmds: A list where each element represents a command to run on the device
    :param excel: the instance of the excel reader parsing the excel hosts file
    :return: None
    """
    try:
        connection = ConnectHandler(**host)
        output = connection.send_config_set(cmds)
        output += connection.save_config()

        # check output record result
        if check_string_not_present(output, check_does_not_contain):
            excel.update_process_column(host["host"], True)
            logger.debug(f"Successfully processed {host['host']}")
            print(f"Successfully processed {host['host']}")
        else:
            excel.update_process_column(host["host"], False)
            logger.debug(f"Failed to  process {host['host']}")
            print(f"Failed to  process {host['host']}")

    except NetmikoAuthenticationException:
        logger.error(f"Auth error exception as {host['host']}")
        excel.update_process_column(host["host"], False)
        return None
    except NetmikoTimeoutException:
        logger.error(f"Timeout error exception {host['host']}")
        excel.update_process_column(host["host"], False)
        return None

    return output

    # # determine whether the results are as expected, and log
    # if validate(output, config_to_check, confirmation_string):
    #     logger.debug(f"{host['host']} configured successfully")
    # else:
    #     logger.debug(
    #         f"{host['host']} loopguard either still enabled or loopguard not observed in spanning tree output"
    #     )


if __name__ == '__main__':
    main()
