# Dynatrace SNMP Polling Extension
A Dynatrace ActiveGate SNMP Polling extension. <br>
Used for monitoring basic health of network devices and other appliances, the ActiveGate will poll for these metrics every minute. Metrics can then be visualised and charted on Dynatrace dashboards and overview pages.<br>

This extension allows Dynatrace to monitor appliances that support standard SNMP MIB objects. You can also adapt this to poll for any SNMP exposed metrics.
* [HOST-RESOURCES-MIB](http://www.net-snmp.org/docs/mibs/host.html)
* [IF-MIB](http://www.net-snmp.org/docs/mibs/interfaces.html)
* **TODO** [CISCO-PROCESS-MIB](http://www.circitor.fr/Mibs/Html/C/CISCO-PROCESS-MIB.php)
* **TODO** Many other standard MIBs

By default this enables us to monitor device metrics
* HOST-RESOURCES-MIB
	- CPU utilisation
	- Memory utilisation - Physical, Virtual, Cached, Buffers
	- Disk Utilisation
* IF-MIB
	- Network Traffic - Incoming/Outgoing
	- Network packets - Incoming/Outgoing
	- Errors - Incoming/Outgoing
	- Discarded packets - Incoming/Outgoing

### Images
See the [Wiki](https://github.com/BraydenNeale/Dynatrace-SNMP/wiki) for example dashboard, OOTB and configuration screens

## Usage
**TO DO** Github Release<br>
Download the `custom.remote.python.snmp-base.zip` and upload to your Dynatrace Environment via **Settings - Monitoring - Monitored technologies.**
You will also need to copy and unzip this to a Linux ActiveGate with a remote plugin module installed at path `/opt/dynatrace/remotepluginmodule/plugin_deployment`<br>

You can restart the Dynatrace remote plugin module via:
* RedHat - `systemctl restart remotepluginmodule`
* Ubuntu - `service remotepluginmodule restart`
<br>**Note: This will not yet run on Windows ActiveGates - See Known Issues for details.** <br>

Once this has been uploaded succesfully you can start to configure monitoring of devices listening for SNMP V2 and V3, using the configuration screen in the Dynatrace UI:
* **Endpoint name** - A display name for the config page - recommended to use hostname.
* **Type of device** - Used for grouping similar devices together, e.g. Cisco Switch, Datapower
* **Hostname/IP of device** - SNMP connection endpoint <HOSTNAME>:<PORT> e.g. mydevice.domain:161
* **SNMP Version** - Version of SNMP to use 2 or 3
* **SNMP User** - The Auth user (V3) or the community name (V2)
* **SNMP v3 Auth protocol** - MD5 or SHA
* **SNMP v3 Auth Key** - The device auth password
* **SNMP v3 Priv Protocol** - AES or DES
* **SNMP v3 Priv Key** - The device priv password
* **Name of the group** - Used for grouping devices belonging to a particular business area, domain...
* **ActiveGate** - The ActiveGate to run this extension polling instance from.
Once configured, you should see an 'Ok' status in the configuration UI and will start to see your device in the Technology overview and metrics availabile for custom charting.

## Development
### Dependencies
* Python3.6
* pysnmp >= 4.4.6
* pysnmp-mibs >= 0.1.6
* requests >= 2.6.0

### Installation
Note: the Dynatrace oneagent comes bundled with Python3.6, so make sure to use Python3.6 when running `oneagent_build_plugin` ([Plugin SDK](https://dynatrace.github.io/plugin-sdk/readme.html)]) as it will compile the correct native cryptodome modules.

#### Setup
`python3.6 -m venv dt-snmp` <br>
`source dt-snmp/bin/activate` <br>
`pip install -r requirements.txt` <br>
Download the Dynatrace plugin SDK from your Dynatrace Environment <br>
`pip install plugin_sdk-1.157.168.20181127.170441-py3-none-any.whl`

#### Building
Files and directories are stipped out when the plugin is built. Because of this the local snmp module gets wiped. I am working out how to bundle this in as a required dependency.
Currently, before building it is required to copy each of the snmp classes - **Poller**, **HostResourceMIB** and **IFMIB** into the main **custom_snmp_base_plugin.py** file.
Make sure to maintain the pysnmp import from Poller. <br>
e.g. custom_snmp_base_plugin_remote.py will resemble
```python
from ... import
# ...

class CustomSnmpBasePluginRemote(RemoteBasePlugin):
	...

from pysnmp.hlapi import *

class Poller():
	...

class HostResourceMIB():
	...

class IFMIB():
	...
```
Also, make sure to remove the snmp/... import statements from the top of the file
```python
#from snmp.host_resource_mib import HostResourceMIB
#from snmp.if_mib import IFMIB
```
Finally, to build run:
`sudo ~/Dev/python/oneagent/bin/oneagent_build_plugin`

#### Testing
To run against the oneagent simulator:<br>
`~/Dev/python/oneagent/bin/oneagent_sim`

To print the SNMP MIB class metrics collected <br>
`python test.py` <br>

#### You can test against a public endpoints with [snmplabs](http://snmplabs.com/snmpsim/public-snmp-agent-simulator.html)
properties.json is already configured to hit demo.snmplabs.com with SNMP version 2<br>
**Testing snmp access and support via the snmpwalk command**<br>
e.g. `snmpwalk -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> demo.snmplabs.com` <br>
**Check IF-MIB support:** <br>
`snmpwalk -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> <HOST> 1.3.6.1.2.1.31.1.1.1.1` <br>
**Check HOST-RESOURCES-MIB support:** <br>
`snmpwal -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> <HOST> 1.3.6.1.2.1.25.2.3.1.2`

## Known Issues
* **Does not yet work for Windows ActiveGates** - `Error(Cannot load native module 'Cryptodome.Cipher._raw_ecb': Trying '_raw_ecb.cp36-win_amd64.pyd': [WinError 126] The specified module could not be found, Trying '_raw_ecb.pyd': [WinError 126] The specified module could not be found)` The modules exist and are compiled correctly... it may just not be using the correct Cryptodome\Util\Cipher\ path
* **No proper error handling implemented yet** - Will be testing and refining this against enteprise appliances, switches and servers soon.
* **Consumes a lot of custom metrics** - I will be adding configuration features to refine Disk and interface dimensions based so that we don't just pull back metrics for 'everything'.

## Contributors
* **[Vu Pham](https://github.com/beantoast)** - Wrote the first custom script for this on site using memcached as ActiveGate extensions were not yet available. See [Branch](https://github.com/BraydenNeale/Dynatrace-SNMP/tree/vu_legacy)
* **[Martin Ribot De Bressac](https://github.com/martinRibotDeBressac)** - Reviewed the original codebase, implemented additional SNMP MIB monitoring for printers.