



# Cisco Command Sender

A simple tool to send commands to a list of Cisco IOS devices.

## Usage

The tool takes two arguments:
1. A file with IP addresses/hostnames. One per line
2. A file with commands to be sent to the devices. Again, one per line.

Run the tool as follows:
```bash
python command_sender.py [-h] [--username USERNAME] [--password PASSWORD] [--log-file] hosts_file cmd_file
```
As an example
```bash
$ python command_sender.py ./data_files/hosts.txt ./data_files/commands.txt
```
## Authentication

You can specifiy username and password on the command line or you can override username and password in the code itself.

**From CLI**

```bash
$ python command_sender.py --username jill --password bob ./data_files/hosts.txt ./data_files/commands.txt
```

**In the code**

```python
# Change
username = args.username if args.username else None
password = args.password if args.password else None

# To
username = args.username if args.username else 'my username here'
password = args.password if args.password else 'my password here'
```

## Hosts File

The program reads a hosts file which must contain a single host per line. A host can be defined by a FQDN or IP address

```text
192.168.2.2
myrouter.mydomain.com
10.10.12.1
```
## Command File

All commands that are to be sent to each host must be defined in the command file. One command per line.

**N.B.** Commands are sent to the configuration prompt, so if a show command is to be executed, then 'do' must be prepended to the command

```text
do show ip int br
vlan 987
name monkey
exit
do show vlan
```

The above is the same as executing the following commands at a Cisco prompt

```bash
switch# conf t
switch(config)# do show ip int br
switch(config)# vlan 987
switch(config-vlan)# name monkey
switch(config-vlan)# exit
switch(config)# do show vlan
```
## Command Checking
The basis of the program is check the output of Cisco commands for the precense of an identifying word in a line, then determine whether or not a keyword is present in that line of text.
As an example, let's look at the use-case where we want to determine whether loopguard is enabled or not on a cisco switch

## Logging

Results are logged and their verbosity levels can be changed. By default, only errors are  sent to the terminal, whereas all log messages are sent to the file handler.

A `results.log` file will look something like this

```
ERROR - 2020-08-13 10:39:02,521 - Timeout error exception 10.10.11.10
ERROR - 2020-08-13 10:39:02,522 - Timeout error exception 10.10.10.10
DEBUG - 2020-08-13 10:39:04,169 - 192.168.2.2 configured successfully
```

`ERROR` denotes that an error occurred, for example, a timeout, or an authentication issue.

`DEBUG` means that this record is for informational purposes only.

### Filtering

To adjust what level of logging appears in which logging output, we need to look at the following code:

```python
# Get an instance of a logger
file_handler = logging.FileHandler(log_file)
stream_handler = logging.StreamHandler(sys.stdout)
file_handler.setLevel(logging.DEBUG)  # I'm setting the logging level for the file based log
stream_handler.setLevel(logging.ERROR)  # And I'm setting the logging level that will appear on screen
# formatting for loggers
file_handler_format = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
stream_handler_format = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
file_handler.setFormatter(file_handler_format)
stream_handler.setFormatter(stream_handler_format)

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)  # I'm the level of logging an event must meet in order to be passed to me.
```

The first thing to take note of is the last line.

```python
logger.setLevel(logging.DEBUG)  # I'm the level of logging an event must meet in order to be passed to me.
```

This sets the logging level for the logging handler known in the code as `logger`. For a logging event to enter the handler, it must be equal to or greater in severity than level passed to `setLevel()`. In this case, all logging messages will go to the `logger` as the level has been set at `DEBUG`

In order to adjust the level of logging for the filehandler, one must change the level in `setLevel()`

```python
file_handler.setLevel(logging.DEBUG)  # I'm setting the logging level for the file based log
```

The same is true for the stream handler (logging to the console)

```python
stream_handler.setLevel(logging.ERROR)  # And I'm setting the logging level that will appear on screen
```

### Log File Desination

By default, the tool will log the results to `results.log` in the same directory as the python file. This can be overriden in the CLI

```
$ python command_sender.py --log-file my_log_file.log ./data_files/hosts.txt ./data_files/commands.txt
```

If can also be overriden directly in the code in order to provide a different default value

```python
# change
log_file = args.log_file if args.log_file else 'results.log'
# to
log_file = args.log_file if args.log_file else 'whatever you want to call it'
```

