#!/bin/bash
# sudo crontab -e
#Poll every 5 minutes
# */5 * * * * /bin/sh /.../DTMonitoring/Schedule/dt_snmp_poll_5_min.sh

/usr/bin/python3 /.../DTMonitoring/Schedule/cisco_vpn_monitoring.py
/usr/bin/python3 /.../DTMonitoring/Schedule/cp_dlp_snmp_monitoring.py
/usr/bin/python3 /.../DTMonitoring/Schedule/cp_sandblast_snmp_monitoring.py
/usr/bin/python3 /.../DTMonitoring/Schedule/f5_swg_snmp_monitoring.py