# DT SNMP Polling Extension
Schedule SNMP polling tasks that post metrics back to Dynatrace.
Used for monitoring basic health of network devices and other appliances.
These metrics can then be charted on Dynatrace dashboards.

Code base initially developed by [Vu Pham](https://github.com/beantoast)
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

TODO - Example images.

**A lot of refinement is required... and IN PROGRESS**

## Usage
**TODO - Properly manage Credentials in OFFLINE config files**
**TODO - Dynatrace plugin UI to add devices**
**TODO - Run as a Dynatrace Remote-Agent Plugin**
**TODO - Remove memcached dependency**
**TODO - Generalise and refactor**

Add you Dynatrace SAAS/Managed environment details
DT_URL_MANAGED = https://<DTM_URL>/e/<ENV_ID>
DT_URL_SAAS = https://<ENV_ID>.live.dynatrace.com
DT_API_TOKEN = <API_TOKEN>

Add your Device snmp details
e.g.
IP = 127.0.0.1
HOSTNAME = locahost
PORT = 161
SNMP_VERSION = 2
SNMP_COMMUNITY = public

`python snmp_monitoring.py`

Sanitised examples Vu had developed are shown in this base directory
* QRadar - qradar_snmp_monitoring.py
* Sandblast - sandblast_snmp_monitoring.py
* UPS - ups_SNMP_monitoring.py
* Cisco VPN - ciscon_SNMP_Monitoring.py
* Checkpoint DLP - cp_dlp_snmp_monitoring.py
...

This is then scheduled to run in 1 or 5 min intervals via Linux cron jobs
See examples under ./Schedule

## Installation
### Dependencies
memcached 1.5.7 (Until Remote-Agent Plugin)
Python3.4+
pysnmp - 4.4.6     
requests - 2.20.0
pymemcache - 2.0.0

### Dev environment 
Install memcache - `yum install memcached`
Install Nix [Nix](https://nixos.org/nix/)
`nix-shell`
`virtualenv dt-snmp-venv`
`source dt-snmp-venv/bin/activate`
`pip install -r requirements.txt`

**TODO Use With SNMP Simulator - Possibly [snmpsim](https://github.com/etingof/snmpsim)**