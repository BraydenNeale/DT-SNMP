# Dynatrace SNMP Polling Extension
Schedule SNMP polling tasks that post metrics back to Dynatrace. <br>
Used for monitoring basic health of network devices and other appliances.<br>
These metrics can then be charted on Dynatrace dashboards. <br>

Code base initially developed by [Vu Pham](https://github.com/beantoast) <br>
**TODO - Convert into a Dynatrace Remote-Agent Plugin**

This extension allows Dynatrace to monitor appliances that support standard MIB objects (You can also adapt this to poll for any SNMP exposed metrics).
* [IF-MIB](http://www.net-snmp.org/docs/mibs/interfaces.html)
* [HOST-RESOURCES-MIB](http://www.net-snmp.org/docs/mibs/host.html)
* [CISCO-PROCESS-MIB](http://www.circitor.fr/Mibs/Html/C/CISCO-PROCESS-MIB.php)

By default this enables us to collect and chart network device metrics
**(TODO - Thresholds for problem detection)**:
* CPU usage
* Memory Usage - Physical, Virtual, Other
* Disk Utilisation
* Network Traffic - Incoming/Outgoing
* Loss Rate - Inbound/Outbound
* Errors - Inbound/Outbound

[Wiki - Example images](https://github.com/BraydenNeale/Dynatrace-SNMP/wiki)

**A lot of refinement is required... and IN PROGRESS**

## Usage
**TODO - Properly manage Credentials in OFFLINE config files** <br>
**TODO - Dynatrace plugin UI to add devices** <br>
**TODO - Run as a Dynatrace Remote-Agent Plugin** <br>
**TODO - Remove memcached dependency** <br>
**TODO - Generalise and refactor** <br>

Add your Dynatrace SAAS/Managed environment details
* DT_URL_MANAGED = https://<DTM_URL>/e/<ENV_ID>
* DT_URL_SAAS = https://<ENV_ID>.live.dynatrace.com
* DT_API_TOKEN = <API_TOKEN>

Add your Device snmp details e.g.
* IP = 127.0.0.1
* HOSTNAME = locahost
* PORT = 161
* SNMP_VERSION = 2
* SNMP_COMMUNITY = public

`python snmp_monitoring.py`

Sanitised examples Vu had developed are shown in this base directory
* QRadar - qradar_snmp_monitoring.py
* Sandblast - sandblast_snmp_monitoring.py
* UPS - ups_SNMP_monitoring.py
* Cisco VPN - ciscon_SNMP_Monitoring.py
* Checkpoint DLP - cp_dlp_snmp_monitoring.py
...

This is then scheduled to run in 1 or 5 min intervals via Linux cron jobs <br>
See examples under ./Schedule

## Installation
### Dependencies
* memcached 1.5.7 (Until Remote-Agent Plugin)
* Python3.4+
* pysnmp - 4.4.6     
* requests - 2.20.0
* pymemcache - 2.0.0

### Dev environment 
* Install memcache - `yum install memcached`
* Install Nix [Nix](https://nixos.org/nix/)
* `nix-shell`
* `virtualenv dt-snmp-venv`
* `source dt-snmp-venv/bin/activate`
* `pip install -r requirements.txt`

**TODO use with an SNMP Simulator - Possibly [snmpsim](https://github.com/etingof/snmpsim)**<br>
You can test against a public service at [snmplabs](http://snmplabs.com/snmpsim/public-snmp-agent-simulator.html)<br>
e.g. `snmpwalk -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> demo.snmplabs.com` <br>
**Check IF-MIB support:** <br>
`snmpwalk -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> <HOST> 1.3.6.1.2.1.31.1.1.1.1` <br>
**Check HOST-RESOURCES-MIB support:** <br>
`snmpwal -v3 -l authPriv -u <USER> -a SHA -A <AUTHKEY> -x AES -X <PRIVKEY> <HOST> 1.3.6.1.2.1.25.2.3.1.2`
