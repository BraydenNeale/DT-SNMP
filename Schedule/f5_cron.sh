#!/bin/bash
# sudo crontab -e
#Poll every 5 minutes
# */5 * * * * /bin/sh /.../DTMonitoring/Schedule/f5_cron.sh

/usr/bin/python3 ../f5_swg_snmp_monitoring.py
