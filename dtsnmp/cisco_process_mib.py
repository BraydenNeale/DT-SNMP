import logging
from .poller import Poller
from .processing import process_metrics, reduce_average, split_oid_index

logger = logging.getLogger(__name__)

class CiscoProcessMIB():
	"""
	Metric processing for CISCO-PROCESS-MIB
	CISCO host and other statistics

	Reference
	http://www.circitor.fr/Mibs/Html/C/CISCO-PROCESS-MIB.php

	Usage
	cisco_mib = CiscoProcessMIB(device, authentication)
	cisco_metrics = cisco_mib.poll_metrics()

	Returns a dictionary containing values for:
	CPU Utilsation
	Memory Utilisation
	"""
	
	mib_name = 'CISCO-PROCESS-MIB'
	mib_endpoints = [
		'1.3.6.1.4.1.9.9.109.1.1.1.1.7',	# cpmCPUTotal1minRev - CPU busy % for the last min
		'1.3.6.1.4.1.9.9.109.1.1.1.1.17', 	# cpmCPUMemoryHCUsed - Memory Used
		'1.3.6.1.4.1.9.9.109.1.1.1.1.19' 	# cpmCPUMemoryHCFree - Memory Free
	]

	def __init__(self, device, authentication):
		self.poller = Poller(device, authentication)
		self.oids = self.mib_endpoints

	def poll_metrics(self):
		gen = self.poller.snmp_connect_bulk(self.oids)
		return process_metrics(gen, calculate_cisco_metrics)

"""
Processing Function to be used with processing.process_metrics
Extracts the following for each interface
cpmCPUTotal1minRev -> varBinds[0]
cpmCPUMemoryHCUsed -> varBinds[1]
cpmCPUMemoryHCFree -> varBinds[2]
"""
def calculate_cisco_metrics(varBinds, metrics):
	cpu = {}
	cpu['value'] = float(varBinds[0][1])
	cpu['dimension'] = None
	cpu['is_absolute_number'] = True

	memory_used = varBinds[1][1]
	memory_free = varBinds[2][1]
	memory_total = memory_used + memory_free
	memory_utilisation = (memory_used / memory_total) * 100
	memory = {}
	memory['value'] = memory_utilisation
	memory['dimension'] = {'Storage': 'System memory'}
	memory['is_absolute_number'] = True


	metrics.setdefault('cpu_utilisation', []).append(cpu)
	metrics.setdefault('memory_utilisation', []).append(memory)
