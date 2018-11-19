from poller import Poller

class HostResourceMIB():
	poller = None
	oids = None

	mib_name = 'HOST-RESOURCES-MIB'

	storage_types = {
		'physical_memory': {
			'size': 'hrStorageSize.1',
			'used': 'hrStorageUsed.1',
		},
		'virtual_memory': {
			'size': 'hrStorageSize.3',
			'used': 'hrStorageUsed.3',
		}
	}

	def __init__(self, device, authentication):
		self.poller = Poller(device, authentication)


	def poll_metrics(self):
		self._poll_cpu()
		self._poll_storage()

	def _poll_cpu(self):
		cpu_metrics = [
		    'hrProcessorLoad',
		]

		oids = [(self.mib_name, metric) for metric in cpu_metrics]
		gen = self.poller.snmp_connect_bulk(oids)
		self._process_cpu(gen)

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
			    for name,value in varBinds:
			    	count += 1
			    	total += value

		print(total / float(count))

	def _poll_storage(self):
		storage_metrics = [
		    'hrStorageDescr',
		    'hrStorageSize',
		    'hrStorageUsed',
		]
		oids = [(self.mib_name, metric) for metric in storage_metrics]
		gen = self.poller.snmp_connect_bulk(oids)

		self._process_storage(gen)

	def _process_storage(self,gen):
		storage = []
		for item in gen:
			errorIndication, errorStatus, errorIndex, varBinds = item
			if errorIndication:
			    print(errorIndication)
			elif errorStatus:
			    print('%s at %s' % (errorStatus.prettyPrint(),
			                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
			else:
				index = {}
				index['desc'] = varBinds[0][1]
				index['size'] = varBinds[1][1]
				index['used'] = varBinds[2][1]
				storage.append(index)
		
		for index in storage:
			utilisation = (index['used'] / float(index['size']))*100
			print("{} - {}%".format(index['desc'], utilisation))

	def _calculate_memory(self, physical_memory, virtual_memory):
		pass

	def _calculate_disk(self, disks):
		pass

