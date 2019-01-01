import logging
from .poller import Poller

logger = logging.getLogger(__name__)

class HostResourceMIB():
	"""
	Metric processing for Host-Resouce-Mib
	Host infrastructure statistics

	This is supported by most device types 

	Reference
	http://www.net-snmp.org/docs/mibs/host.html

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
		memory, disk = self._poll_storage()

		metrics = {
			'cpu_utilisation': cpu,
			'memory_utilisation': memory,
			'disk_utilisation': disk
		}

		return metrics

	def _poll_cpu(self):
		cpu_metrics = [
		    'hrProcessorLoad',
		]
		oids = [(self.mib_name, metric) for metric in cpu_metrics]
		gen = self.poller.snmp_connect_bulk(oids)
		return self._process_cpu(gen)

	def _process_cpu(self,gen):
		count = 0
		total = 0
		processors = []
		for item in gen:
			errorIndication, errorStatus, errorIndex, varBinds = item
			if errorIndication:
			    logger.error(errorIndication)
			elif errorStatus:
			    logger.error('%s at %s' % (errorStatus.prettyPrint(),
			                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
			else:
				# Calculate average - Not each seperate index
			    for name, value in varBinds:
		    		count += 1
		    		total += float(value)

		if (count > 0):
			cpu = {}
			# No dimension is the default and handled gracefully by the SDK
			cpu['dimension'] = None
			cpu['value'] = total / count
			cpu['is_absolute_number'] = True
			processors.append(cpu)

		return processors

	def _poll_storage(self):
		storage_metrics = [
		    'hrStorageDescr',
		    'hrStorageSize',
		    'hrStorageUsed',
		]
		oids = [(self.mib_name, metric) for metric in storage_metrics]
		gen = self.poller.snmp_connect_bulk(oids)

		return self._process_storage(gen)

	def _process_storage(self,gen):
		memory = []
		disk = []
		memory_types = ['memory', 'swap space', 'ram']
		for item in gen:
			errorIndication, errorStatus, errorIndex, varBinds = item
			if errorIndication:
			    logger.error(errorIndication)
			elif errorStatus:
			    logger.error('%s at %s' % (errorStatus.prettyPrint(),
			                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
			else:
				name = ''
				for varBind in varBinds:
					name = varBinds[0][1].prettyPrint()
					size = float(varBinds[1][1])
					used = float(varBinds[2][1])
					utilisation = (used / size)*100
					storage = {}
					storage['dimension'] = {'Storage': name}
					storage['value'] = utilisation
					storage['is_absolute_number'] = True

				# Memory metrics as a dimension under memory_utilisation
				if any(x in name.lower() for x in memory_types):
					memory.append(storage)
				else:
					disk.append(storage)
		
		return memory, disk
