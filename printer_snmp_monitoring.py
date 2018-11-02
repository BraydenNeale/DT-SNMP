# ==========================================
# 
# printer snmp monitoring
# 
# takes 2'14" to complete on 13 hosts
# - add threading
# down to 44" through queue/threading
# - 5 threads was causing the data to glitch out
# tests my skills with threading
# 
# ==========================================

import queue
import threading
from dtmon.dt_printer_snmp import dt_printer_mon

class Worker(threading.Thread):
    def __init__(self, q, other_arg, *args, **kwargs):
        self.workspace = {}
        self.q = q
        self.other_arg = other_arg
        super().__init__(*args, **kwargs)
    def run(self):
        while True:
            try:
                work = self.q.get(timeout=3)  # 3s timeout
            except queue.Empty:
                return
            print((work, self.other_arg))
            self.printer_run(work)
            self.q.task_done()

    def printer_run(self, hosts):
        workspace_id = hosts["host"]
        dtendpoint = {
            "url": "<DT_URL>",
            "apiToken": "<API>"
        }

        if "xerox" in hosts["printer_type"]:
            printer_type = "Xerox Printer"
            printer_id = "xerox.printer"
            printer_tags = ["Xerox Printer", "Xerox", "Printer"]
        else:
            printer_type = "Ricoh Printer"
            printer_id = "ricoh.printer"
            printer_tags = ["Ricoh Printer", "Ricoh", "Printer"]

        printer_endpoint = {
            "host": hosts["ip"],
            "port": 161,
            "snmpAuth": {
                "version": 2,
                "username": "<COMMUNITY_STRING>"
            }
        }

        deviceDisplay = {
            "id": "domain." + printer_id + "." + hosts["host"] + "domain", 
            "name": printer_type + " | " + hosts["host"] + "domain", 
            "type": printer_type,
            "ips": [hosts["ip"]], 
            "ports":["161"],
            # "configConsoleUrl":"",
            "tags": printer_tags,
            "icon":"http://assets.dynatrace.com/global/icons/infographic_rack.png"
        }

        logDetails = {"level":"debug", "location": "./printer_snmp_monitoring.log"}
        self.workspace.update({workspace_id: dt_printer_mon(dtendpoint, printer_endpoint, deviceDisplay, logDetails=logDetails)})
        self.workspace[workspace_id].dtrun()
        return

def main():
    printer_hosts_dict = [
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "xerox" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "ricoh" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "ricoh" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "xerox" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "xerox" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "xerox" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "xerox" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "xerox" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "ricoh" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "ricoh" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "ricoh" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "ricoh" },
        { "host": "<HOSTNAME>", "ip": "<IP>", "printer_type": "xerox" }
    ]

    q = queue.Queue()
    for hosts in printer_hosts_dict:
        q.put_nowait(hosts)
    for _ in range(4):
        Worker(q, _).start()
    q.join()  # blocks until the queue is empty.

if __name__ == '__main__':
    main()