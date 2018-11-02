#!/bin/bash
# sudo crontab -e
#Poll every 5 minutes
# */5 * * * * /bin/sh /.../DTMonitoring/Schedule/cp_sandblast_cron.sh

/usr/bin/python3 ../cp_sandblast_snmp_monitoring.py
