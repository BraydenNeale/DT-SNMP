from poller import Poller

class IFMIB():
	poller = None
	oids = None

	mib_name = 'IF-MIB'
	mib_metrics = [
	    'ifInOctets', # Incoming Traffic
	    'ifHCOutOctets', # Outgoing Traffic,
	    'ifInErrors', # Incoming errors
	    'ifOutErrors', # Outgoing errors
	    'ifInDiscards', # Incoming loss rate
	    'ifOutDiscards', # Outgoing loss rate
	    'ifInUcastPkts',
	    'ifOutUcastPkts',
	]

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
