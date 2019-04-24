import logging
from .poller import Poller
from .processing import process_metrics, reduce_average, split_oid_index

logger = logging.getLogger(__name__)

class HostResourceMIB():
	"""
	Metric processing for Host-Resouce-Mib
	Host infrastructure statistics

	This is supported by most device types 

	Reference
	http://www.net-snmp.org/docs/mibs/host.html
	https://www.oidview.com/mibs/0/HOST-RESOURCES-MIB.html

	Usage
	hr_mib = HostResourceMIB(device, authentication)
	host_metrics = hr_mib.poll_metrics()

	Returns a dictionary containing values for:
	cpu, memory, disk

	TODO implement disk splits
	"""

	mib_name = 'HOST-RESOURCES-MIB'

	def __init__(self, device, authentication):
		self.poller = Poller(device, authentication)

	def poll_metrics(self):
		cpu = self._poll_cpu()
		storage = self._poll_storage()

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
		cpu_metrics = [
		    '1.3.6.1.2.1.25.3.3.1.2'	# hrProcessorLoad
		]
		
		gen = self.poller.snmp_connect_bulk(cpu_metrics)
		return process_metrics(gen, calculate_cpu_metrics)

	def _poll_storage(self):
		storage_metrics = [
			'1.3.6.1.2.1.25.2.3.1.3',	# hrStorageDescr
			'1.3.6.1.2.1.25.2.3.1.5',	# hrStorageSize
			'1.3.6.1.2.1.25.2.3.1.6'	# hrStorageUsed
		]

		gen = self.poller.snmp_connect_bulk(storage_metrics)
		return process_metrics(gen, calculate_storage_metrics)

"""
Processing Function to be used with processing.process_metrics
Extracts the CPU utilisation for each index
hrProcessorLoad -> varBinds[0]
"""
def calculate_cpu_metrics(varBinds, metrics):
	cpu = {}
	index = split_oid_index(varBinds[0][0])
	cpu['value'] = float(varBinds[0][1])
	cpu['dimension'] = {'Index': index}
	cpu['is_absolute_number'] = True
	metrics.setdefault('cpu', []).append(cpu)

"""
Processing Function to be used with processing.process_metrics
Extracts the storage itilisation - splitting into memory/disk types
hrStorageDescr -> varBinds[0]
hrStorageSize -> varBinds[1]
hrStorageUsed -> varBinds[2]
"""
def calculate_storage_metrics(varBinds, metrics):
	memory_types = ['memory', 'swap space', 'ram']

	name = varBinds[0][1].prettyPrint()
	size = float(varBinds[1][1])
	used = float(varBinds[2][1])
	utilisation = 0
	# Division by 0 exception - e.g. Swap Space 0 used of 0
	if size > 0:
		utilisation = (used / size)*100

	storage = {}
	storage['dimension'] = {'Storage': name}
	storage['value'] = utilisation
	storage['is_absolute_number'] = True

	# Memory metrics as a dimension under memory_utilisation
	if any(x in name.lower() for x in memory_types):
		metrics.setdefault('memory', []).append(storage)
	else:
		metrics.setdefault('disk', []).append(storage)

