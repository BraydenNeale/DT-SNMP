# Dynatrace SNMP Polling Extension
Schedule SNMP polling tasks that post metrics back to Dynatrace.<br>
Used for monitoring basic health of network devices and other appliances.<br>
These metrics can then be charted on Dynatrace dashboards.<br>

#### Code base developed by [Vu Pham](https://github.com/beantoast)

This extension allows Dynatrace to monitor appliances that support standard MIB objects (You can also adapt this to poll for any SNMP exposed metrics).
* [IF-MIB](http://www.net-snmp.org/docs/mibs/interfaces.html)
* [HOST-RESOURCES-MIB](http://www.net-snmp.org/docs/mibs/host.html)
* [CISCO-PROCESS-MIB](http://www.circitor.fr/Mibs/Html/C/CISCO-PROCESS-MIB.php)

By default this enables us to collect and chart network device metrics
* CPU usage
* Memory Usage - Physical, Virtual, Other
* Disk Utilisation
* Network Traffic - Incoming/Outgoing
* Loss Rate - Inbound/Outbound
* Errors - Inbound/Outbound

This runs without an Activegate or SDK and posts collected metrics directly to the [DYNATRACE API](https://www.dynatrace.com/support/help/dynatrace-api/) endpoints <br>

## Usage
Add your Dynatrace and Device endpoints and configuration to the relevant snmp_monitoring.py file in the base directory<br>

**Example**
```python
dtendpoint = {
	"url": "<DT_URL>",
	"apiToken": "<API_TOKEN>"
}
	
deviceEndpoint = {
	"host": "<IP>",
	"port": 161,
	"snmpAuth": {
		"version": 3,
		"username": "<USEER>",
		"authKey": "<AUTH_KEY>",
		"privKey": "<PRIV_KEY>",
		"authProtocol": "<AUTH_PROT>",
		"privProtocol": "<PRIV_PROT>"
	}
}

deviceDisplay = {
	"id": "<DOMAIN>.<VENDOR_NAME>.<DEVICE_NAME>.<HOST_NAME>", 
	"displayName": "<HOST_NAME> | <DEVICE_NAME>", 
	"type": "<DEVICE_NAME>",
	"ipAddresses":["<IP>"], 
	"listenPorts":["<PORT>"], 
	"tags": ["<TAG>"],
	"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
	"groupId": "<GROUP>",
	"properties": {}
}

logDetails = {"level":"debug", "location": "./DTExampleSNMPMon.log"}

example = DTExampleMon(dtendpoint, exampleEndpoint, deviceDisplay, logDetails=logDetails, getLatency=True, mib={"use": False})
t_example = example.dtrun()
t_example.join()
```

And then run with<br>
`python snmp_monitoring.py`

Sanitised examples are shown in this base directory
* QRadar - qradar_snmp_monitoring.py
* Sandblast - sandblast_snmp_monitoring.py
* UPS - ups_SNMP_monitoring.py
* Cisco VPN - ciscon_SNMP_Monitoring.py
* Checkpoint DLP - cp_dlp_snmp_monitoring.py
...

This is then scheduled to run in 1 or 5 min intervals via Linux cron jobs <br>
See an example under ./Schedule

## Installation
### Dependencies
* memcached 1.5.7
* Python3.4+
* pysnmp - 4.4.6     
* requests - 2.20.0
* pymemcache - 2.0.0

### Dev environment 
* Install memcached - `yum install memcached`
* `python3 -m venv dt-snmp`
* `source dt-snmp/bin/activate`
* `pip install -r requirements.txt`


### You can test against a public service at [snmplabs](http://snmplabs.com/snmpsim/public-snmp-agent-simulator.html)<br>
e.g. `snmpwalk -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> demo.snmplabs.com` <br>
#### Check IF-MIB support:
`snmpwalk -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> <HOST> 1.3.6.1.2.1.31.1.1.1.1` <br>
#### Check HOST-RESOURCES-MIB support:
`snmpwal -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> <HOST> 1.3.6.1.2.1.25.2.3.1.2`
