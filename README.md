# DT SNMP Polling Extension
## Dynatrace now supports monitoring of generic SNMP devices through an **Official** v2 extension. You can enable and use this today from the [Dynatrace HUB](https://www.dynatrace.com/hub/detail/snmp-generic/?query=generic)
## You can also create your own using the declarative SNMP extensions: [Dynatrace SNMP-Extension](https://www.dynatrace.com/support/help/shortlink/snmp-extension)

---

<h2 style="color:orange">WARNING: This is a community plugin and is not officially supported by Dynatrace</h2>
<h2 style="color:orange">WARNING: This Extension is also no longer updated or maintained. Use the official Dynatrace SNMP monitoring capabilities instead</h2>

**A Dynatrace ActiveGate SNMP Polling v1 extension.** <br>
Used for monitoring basic health of network devices and other appliances, the ActiveGate will poll for these metrics every minute. Metrics can then be visualised and charted on Dynatrace dashboards and overview pages.<br>
The goal is to be as device compatible and general as possible.<br>

This extension enables Dynatrace to monitor basic device health metrics.
* HOST (CISCO-MIB, F5-MIB or Host-RESOURCE-MIB)
	- CPU utilisation
	- Memory utilisation
	- Disk Utilisation
* NETWORK (IF-MIB)
	- Network Traffic - Incoming/Outgoing
	- Network packets - Incoming/Outgoing
	- Errors - Incoming/Outgoing
	- Discarded packets - Incoming/Outgoing

and properties:
* SNMPv2-MIB
	- sysDescr
	- sysObjectID
	- sysUpTime
	- sysContact
    - sysName
	- sysLocation
	- sysServices
	- sysORLastChange


It makes use of the following MIBs:
* DEFAULT
	- [SNMPv2-MIB](http://www.oidview.com/mibs/0/SNMPv2-MIB.html)
	- [HOST-RESOURCES-MIB](http://www.net-snmp.org/docs/mibs/host.html)
	- [IF-MIB](http://www.net-snmp.org/docs/mibs/interfaces.html)
* CISCO
	- [CISCO-PROCESS-MIB](http://www.circitor.fr/Mibs/Html/C/CISCO-PROCESS-MIB.php)
	- [CISCO-ENHANCED-MEMPOOL-MIB](http://www.oidview.com/mibs/9/CISCO-ENHANCED-MEMPOOL-MIB.html)
* F5
	- [F5-BIGIP-SYSTEM-MIB](http://www.circitor.fr/Mibs/Html/F/F5-BIGIP-SYSTEM-MIB.php)


**You can fork and adapt this to poll for any SNMP exposed metrics**

To learn more about Dynatrace ActiveGate extensions see - [ActiveGate Plugins](https://www.dynatrace.com/support/help/extend-dynatrace/dynatrace-sdks/activegate-plugins/)<br>
**This extension consumes custom metrics, for an understanding of how custom metrics are licensed and consumed in Dynatrace, see: [Calculate Monitoring Consumption](https://www.dynatrace.com/support/help/get-started/reference/calculate-monitoring-consumption/)**

### Images
See the [Wiki](https://github.com/BraydenNeale/Dynatrace-SNMP/wiki) for example dashboard, OOTB and configuration screens

## Usage
Download the [Latest relase](https://github.com/BraydenNeale/DT-SNMP/releases) `custom.remote.python.snmp-base.zip` and upload to your Dynatrace Environment via **Settings - Monitoring - Monitored technologies.**
You will also need to copy and unzip this to a Linux ActiveGate with a remoteplugin module installed at path `/opt/dynatrace/remotepluginmodule/plugin_deployment`<br>

You can restart the Dynatrace remote plugin module via:
* RedHat - `systemctl restart remotepluginmodule`
* Ubuntu - `service remotepluginmodule restart`
<br>**Note: This will not run from Windows ActiveGates - See Known Issues for details.** <br>

**Basically, from your Linux ActiveGate with the Dynatrace remotepluginmodule running**
* `wget https://github.com/BraydenNeale/DT-SNMP/releases/download/1.023/custom.remote.python.snmp-base.zip`
* `mv custom.remote.python.snmp.base.zip /opt/dynatrace/remotepluginmodule/plugin_deployment`
* `unzip custom.remote.python.snmp.base.zip`
* `systemctl restart remotepluginmodule`

Once this has been uploaded succesfully you can start to configure monitoring of devices listening for SNMP V2 and V3, using the [Configuration screen](https://github.com/BraydenNeale/DT-SNMP/wiki#configuration) in the Dynatrace web UI:
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

For more information: See Dynatrace documentation: [How to deploy an activegate plugin](https://www.dynatrace.com/support/help/extend-dynatrace/extensions/development/extension-how-tos/deploy-an-activegate-plugin/)

### Errors
* Use Github [Issues](https://github.com/BraydenNeale/DT-SNMP/issues) to help with any specific error troubleshooting 
* Some generic troubleshooting steps are also documented at [Dynatrace troubleshoot extension](https://www.dynatrace.com/support/help/extend-dynatrace/extensions/troubleshooting/troubleshoot-extensions/)

## Development
Refer to this section if you are wanting to extend this to poll for other metrics or to be device specific.
A Dynatrace ActiveGate extension tutorial is available at: [ActiveGate extensions tutorial](https://www.dynatrace.com/support/help/extend-dynatrace/extensions/activegate-extensions/write-your-first-activegate-plugin/)

### Dependencies
* Python3.6
* pysnmp >= 4.4.6

### Installation
Note: the Dynatrace oneagent comes bundled with Python3.6, so make sure to use Python3.6 when running `oneagent_build_plugin` ([Plugin SDK](https://dynatrace.github.io/plugin-sdk/readme.html)) as it will compile the correct native cryptodome modules.

#### Setup
`python3.6 -m venv dtsnmp` <br>
`source dtsnmp/bin/activate` <br>
`pip install -r requirements.txt` <br>
Download the Dynatrace plugin SDK from your Dynatrace Environment <br>
`pip install plugin_sdk-1.157.168.20181127.170441-py3-none-any.whl`

#### Building
1. `sudo .../dtsnmp/bin/oneagent_build_plugin` - sdk build

Run the SDK command: `sudo .../dtsnmp/bin/oneagent_build_plugin` <br>
This will fetch dependencies in plugin.json, compile and bundle everything together under: **/opt/dynatrace/remotepluginmodule/plugin_deployment/custom.remote.python.snmp-base.zip** - Linux

#### Adding another MIB
To add support for another MIB and to poll for additional SNMP metrics, add and import an additional class under the dtsnmp module. It is expected to implement the **poll_metrics** function. Each metric is expected to have the following properties:
* **value**: The value of the metric (must be convertible to float)
* **dimension**: A dictionary containing the dimension name and value (Strings): `name: value`. If there is no dimension to split the metric on, then explicitly set this to None as that is handled as default by the SDK.
* **is_absolute_number**: A boolean, whether or not the metric is absolute or relative
	- Absolute: Independent, stand alone
	- Relative: Dependent on previous value e.g. Counter

e.g.
```python
class CustomMIB():
	def __init__(self, device, authentication):
		self.poller = Poller(device, authentication)

	def poll_metrics(self):
		metrics = {
			'metric1': [
				{
					'dimension': None
					'is_absolute_number': True,
					'value: value'
				}
			],
			'metric2': [
				{
					'dimension': {'Name': 'value'}
					'is_absolute_number': False,
					'value: value'
				},
				{
					'dimension': {'Name': 'value'}
					'is_absolute_number': False,
					'value: value'
				}
			]
		}

		return metrics
```
Once defined, you can simply add it to the mib_list in **custom_snmp_base_plugin_remote.py** e.g. 
```python
# Custom MIB
custom_mib = CustomMib(device, authentication)
mib_list.append(custom_mib)
```
e.g. The metric format for Host-Resources-MIB and IF-MIB is:
```python
#HOST_RESOURCE_MIB 
{
	'cpu_utilisation': [
		{
			'dimension': None,
			'is_absolute_number': True,
			'value': 11.0
		}
	],
	'disk_utilisation': [
		{
			'dimension': {'Storage': '/'}, 
			'is_absolute_number': True,
			'value': 77.06483354871978
		},
		{
			'dimension': {'Storage': '/usr/local'},
			'is_absolute_number': True,
			'value': 79.05778271288935
		},
		...
	]
	'memory_utilisation': [
		{
			'dimension': {'Storage': 'Physical memory'},
 			'is_absolute_number': True,
 			'value': 93.7571919497131
		},
		{
			'dimension': {'Storage': 'Virtual memory'},
			'is_absolute_number': True,
			'value': 49.03610213914279
		},
		...
	]
}

# IF_MIB
{
	'incoming_traffic': [
		{
			'dimension': {'Interface': '1'},
			'is_absolute_number': False,
			'value': 415496409580240.0
		},
		{
			'dimension': {'Interface': '2'},
			'is_absolute_number': False,
			'value': 321564641040573.0,
		}
	],
	'outgoing_traffic': [
		{
			'dimension': {'Interface': '1'},
			'is_absolute_number': False,
			'value': 427663219773201.0,
		}
		{
			'dimension': {'Interface': '2'},
			'is_absolute_number': False,
			'value': 295719899494783.0
		}
	],
	...
}
```
You can Create an instance of the **Poller** class to handle SNMP connections and call **process_metrics** in **processing.py** with a custom function for metric extraction and calculations.

You must also register your custom metrics by adding them to **plugin.json** under "metrics". e.g.
```javascript
"metrics":[
   {
      "entity": "CUSTOM_DEVICE",
      "timeseries":{
         "key":"cpu_utilisation",
         "unit":"Percent",
         "displayname":"CPU utilisation"
      }
   },
   ...
   {
      "entity": "CUSTOM_DEVICE",
      "timeseries":{
         "key":"incoming_traffic",
         "unit":"Byte",
         "displayname":"Incoming traffic",
         "dimensions": ["Interface"]
      }
   },
   ...
]
```
#### Testing
To run against the oneagent simulator:<br>
`.../dtsnmp/bin/oneagent_sim`

To print the SNMP MIB class metrics collected <br>
`python test.py` <br>

#### You can test against public endpoints with [snmplabs](http://snmplabs.com/snmpsim/public-snmp-agent-simulator.html)
properties.json is already configured to hit demo.snmplabs.com with SNMP version 2<br>
**Testing snmp access and support via the snmpwalk command**<br>
e.g. `snmpwalk -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> demo.snmplabs.com` <br>
**Check IF-MIB support:** <br>
`snmpwalk -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> <HOST> 1.3.6.1.2.1.31.1.1.1.1` <br>
**Check HOST-RESOURCES-MIB support:** <br>
`snmpwal -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> <HOST> 1.3.6.1.2.1.25.2.3.1.2`

## Known Issues
* **Does not yet work for Windows ActiveGates** - `Error(Cannot load native module 'Cryptodome.Cipher._raw_ecb': Trying '_raw_ecb.cp36-win_amd64.pyd': [WinError 126] The specified module could not be found, Trying '_raw_ecb.pyd': [WinError 126] The specified module could not be found)` The modules exist and are compiled correctly... it may just not be using the correct Cryptodome\Util\Cipher\ path

## Contributors
* **[Vu Pham](https://github.com/beantoast)** - Wrote the first custom script for this on site using memcached as ActiveGate extensions were not yet available. See [Branch](https://github.com/BraydenNeale/Dynatrace-SNMP/tree/vu_legacy)
* **[Martin Ribot De Bressac](https://github.com/martinRibotDeBressac)** - Reviewed the original codebase, implemented additional SNMP MIB monitoring for printers.
