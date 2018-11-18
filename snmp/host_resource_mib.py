from poller import Poller

class HostResourceMIB():
	poller = None
	oids = None

	mib_name = 'HOST-RESOURCES-MIB'
	mib_metrics = [
	    'hrProcessorLoad', # CPU Utilisation
	    #'hrStorageType',
	    #'hrStorageDescr',
	    #'hrStorageSize',
	    #'hrStorageUsed',
	]

	cpu_usage = 'hrProcessorLoad'

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
		self.oids = [(self.mib_name, metric) for metric in self.mib_metrics]


	def poll_metrics(self):
		gen = self.poller.snmp_connect_bulk(self.oids)
		self._process_result(gen)

	def _process_result(self,gen):
		cpu_index_list = []
		for item in gen:
			errorIndication, errorStatus, errorIndex, varBinds = item

			if errorIndication:
			    print(errorIndication)
			elif errorStatus:
			    print('%s at %s' % (errorStatus.prettyPrint(),
			                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
			else:
			    for name,value in varBinds:
			    	if self.cpu_usage in name.prettyPrint():
			    		cpu_index_list.append(value)

		average_cpu = self._calculate_cpu(cpu_index_list)
		print(average_cpu)

	def _calculate_cpu(self, cpu_index):
		return sum(cpu_index) / float(len(cpu_index))

