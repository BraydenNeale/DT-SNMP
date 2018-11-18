from poller import Poller

class HostResourceMIB():
	poller = None
	oids = None

	mib_name = 'HOST-RESOURCES-MIB'
	mib_metrics = [
	    'hrProcessorLoad', # CPU Utilisation
	    #'hrStorageType',
	    'hrStorageDescr',
	    'hrStorageSize',
	    'hrStorageUsed',
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
		for item in gen:
		    errorIndication, errorStatus, errorIndex, varBinds = item
		    
		    if errorIndication:
		        print(errorIndication)
		    elif errorStatus:
		        print('%s at %s' % (errorStatus.prettyPrint(),
		                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
		    else:
		        for varBind in varBinds:
		            print(' = '.join([x.prettyPrint() for x in varBind]))

