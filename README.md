



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
The basis of the program is check the output of Cisco commands for the precense of an identifying word in a line, then determine whether or not a keyword is present in that line of text. In short, we are:

* Defining a command which generates output
* Defining a string which identifies a line(s) we are interested in
* Defining a string which we will use to determine something about the above line.

As an example, let's look at the use-case where we want to determine whether `loopguard` is enabled or not on a cisco switch.

In order to check whether `loopguard` is enabled on a Cisco switch, we must execute the command

`switch#show spanning-tree summary `

We would get output similar to the following depending on how the switch was configured.

```switch#show spanning-tree summary 
Switch is in rapid-pvst mode
Root bridge for: VLAN0001, VLAN0010, VLAN0020, VLAN0100, VLAN0200, VLAN0300
  VLAN0987, VLAN0999
EtherChannel misconfig guard is enabled
Extended system ID           is enabled
Portfast Default             is disabled
PortFast BPDU Guard Default  is disabled
Portfast BPDU Filter Default is disabled
Loopguard Default            is disabled
UplinkFast                   is disabled
BackboneFast                 is disabled
Configured Pathcost method used is short
```

Here we can see that there is a line which reads:

 `Loopguard Default            is disabled`. 

Using this and the logic we defined above, we can find a line with the text `Loopgaurd Default` and determine whether loopguard is running or not by searching for `is disabled`.

To do this in the program, we define two variables and assign them the values in which we are interested

```python
# what we are checking for
# effectively we want to confirm wether some string in present in another string
# for example, by looking at the output of 'show spanning-tree summary'
# we want to confirm whether 'Loopguard Default' is enabled or disabled.
config_to_check = "Loopguard Default"
confirmation_string = "is disabled"
```

These two variables are then passed into a method called `validate()` in the code:

```python
# determine whether the results are as expected, and log
if validate(output, config_to_check, confirmation_string):
    logger.debug(f"{host['host']} configured successfully")
else:
    logger.debug(
        f"{host['host']} loopguard either still enabled or loopguard not observed in spanning tree output"
    )
```

`validate()` simply returns the method `analyse_output_key_value(text_input, key, value)` which is where the actual work is done.

```python
def analyse_output_key_value(text_input, key, value):
    for line in text_input.split("\n"):
        if key in line:
            return True if value in line else False
    return False
```

The reason that `validate()` exists at all is to all it to be extended should it be required to perform additional validation steps

```python
def validate(output, config_to_check, confirmation_string):
    return analyse_output_key_value(output, config_to_check, confirmation_string)
```



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

