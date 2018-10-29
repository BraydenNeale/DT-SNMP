#!/bin/bash
# sudo crontab -e
#Poll every 5 minutes
# */5 * * * * /bin/sh /.../DTMonitoring/Schedule/cisco_vpn_cron.sh

/usr/bin/python3 /.../DTMonitoring/Schedule/cisco_vpn_monitoring.py
