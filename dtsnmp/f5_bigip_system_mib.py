import logging
from .poller import Poller
from .processing import process_metrics, reduce_average, split_oid_index

logger = logging.getLogger(__name__)

class F5BigIPSystemMIB():
	"""
	Metric processing for F5-BIGIP-SYSTEM-MIB
	F5 CPU and memory from the Trafic Management Module (TMM)

	Reference
	http://www.circitor.fr/Mibs/Html/F/F5-BIGIP-SYSTEM-MIB.php

	Usage
	f5_mib = F5BigIPSystemMIB(device, authentication)
	f5_metrics = f5_mib.poll_metrics()

	Returns a dictionary containing values for:
	CPU Utilsation
	Memory Utilisation
	"""

	def __init__(self, device, authentication):
		self.poller = Poller(device, authentication)

	def poll_metrics(self):
		cpu = self._poll_cpu()
		storage = self._poll_memory()

		cpu_utilisation = cpu.get('cpu', [])
		memory = storage.get('memory', [])
		disk = storage.get('disk', [])

		metrics = {
			'cpu_utilisation': cpu_utilisation,
			'memory_utilisation': memory,
			'disk_utilisation': disk
		}
		return metrics

	def _poll_cpu(self):
		# CPU UTIL of BIG-IP: https://support.f5.com/csp/article/K28455051
		# sysGlobalHostCpuUsageRatio1m may be better than just TMM
		cpu_endpoints = [
		 	'1.3.6.1.4.1.3375.2.1.8.2.3.1.38'   # sysTmmStatTmUsageRatio1m - % of time TMM CPU busy
		]
		gen = self.poller.snmp_connect_bulk(cpu_endpoints)
		return process_metrics(gen, calculate_f5_cpu)

	def _poll_memory(self):
		memory_endpoints = [
			'1.3.6.1.4.1.3375.2.1.1.2.1.143',	# sysStatMemoryTotalKb - Memory Total
			'1.3.6.1.4.1.3375.2.1.1.2.1.144'	# sysStatMemoryUsedKb - Memory Used
		]
		gen = self.poller.snmp_connect_bulk(memory_endpoints)
		return process_metrics(gen, calculate_f5_memory)

"""
sysTmmStatTmUsageRatio1m -> varBinds[0]
"""
def calculate_f5_cpu(varBinds, metrics):
	cpu = {}
	index = split_oid_index(varBinds[0][0])
	cpu['value'] = float(varBinds[0][1])
	cpu['dimension'] = {'Index': index}
	cpu['is_absolute_number'] = True
	metrics.setdefault('cpu', []).append(cpu)
"""
sysStatMemoryTotalKb -> varBinds[0]
sysStatMemoryUsedKb -> varBinds[1]
"""
def calculate_f5_memory(varBinds, metrics):
	memory_name = 'Traffic Management Microkernel'
	memory_total = float(varBinds[0][1])
	memory_used = float(varBinds[1][1])
	memory_utilisation = 0
	if memory_total > 0:
		memory_utilisation = (memory_used / memory_total) * 100
	
	memory = {}
	memory['value'] = memory_utilisation
	memory['dimension'] = {'Storage': memory_name}
	memory['is_absolute_number'] = True

	metrics.setdefault('memory', []).append(memory)
