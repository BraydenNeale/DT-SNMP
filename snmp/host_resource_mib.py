from .poller import Poller

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
			'cpu': cpu,
			'memory': memory,
			#'disk': disk,
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
		for item in gen:
			errorIndication, errorStatus, errorIndex, varBinds = item
			if errorIndication:
			    print(errorIndication)
			elif errorStatus:
			    print('%s at %s' % (errorStatus.prettyPrint(),
			                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
			else:
				# 1 index per iteration
			    for name, value in varBinds:
		    		count += 1
		    		total += value

		return (total / float(count))

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
		storage = []
		memory_name = 'Physical memory'
		memory = 0
		for item in gen:
			errorIndication, errorStatus, errorIndex, varBinds = item
			if errorIndication:
			    print(errorIndication)
			elif errorStatus:
			    print('%s at %s' % (errorStatus.prettyPrint(),
			                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
			else:
				index = {}
				index['descriptor'] = varBinds[0][1].prettyPrint()
				size = varBinds[1][1]
				used = varBinds[2][1]
				index['utilisation'] = (used / float(size))*100

				if index['descriptor'] == memory_name:
					memory = index['utilisation']
					# TODO handle disk splitting
					break
				else:	
					storage.append(index)
		
		return memory, storage
