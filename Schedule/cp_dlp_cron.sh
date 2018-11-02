#!/bin/bash
# sudo crontab -e
#Poll every 5 minutes
# */5 * * * * /bin/sh /.../DTMonitoring/Schedule/cp_dlp_cron.sh

/usr/bin/python3 ../cp_dlp_snmp_monitoring.py
