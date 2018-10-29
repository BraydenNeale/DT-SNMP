DT Custom SNMP Polling

TODO - properly

Dev environment (Seperate dependencies)
nix-shell
virtualenv dt-snmp-venv
source dt-snmp-venv/bin/activate
pip install -r requirements.txt

Run:
python snmp_monitoring.py

Install dependencies in custom_extension_dependencies.tar.gz
and set up 1min or 5min cron jobs for schedules polling
