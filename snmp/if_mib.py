from snmp.poller import Poller

class IFMIB():
	poller = None
	oids = None

	mib_name = 'IF-MIB'
	mib_metrics = [
		'ifSpeed', # Bandwidth
	    'ifHCInOctets', # Incoming Traffic
	    'ifHCOutOctets', # Outgoing Traffic,
	    'ifInErrors', # Incoming errors
	    'ifOutErrors', # Outgoing errors
	    'ifInDiscards',
	    'ifOutDiscards',
	    'ifHCInUcastPkts',
	    'ifHCInBroadcastPkts',
	    'ifHCInMulticastPkts',
	    'ifHCOutUcastPkts',
	    'ifHCOutBroadcastPkts',
	    'ifHCOutMulticastPkts',
	]
	# Mib reference
	# http://cric.grenoble.cnrs.fr/Administrateurs/Outils/MIBS/?oid=1.3.6.1.2.1.31.1.1.1
	# http://www.net-snmp.org/docs/mibs/interfaces.html

	def __init__(self, device, authentication):
		self.poller = Poller(device, authentication)
		self.oids = [(self.mib_name, metric) for metric in self.mib_metrics]

	def poll_metrics(self):
		gen = self.poller.snmp_connect_bulk(self.oids)
		self._process_result(gen)

	def _process_result(self,gen):
		#interfaces = []
		metrics = {}
		for item in gen:
		    errorIndication, errorStatus, errorIndex, varBinds = item
		    
		    if errorIndication:
		        print(errorIndication)
		    elif errorStatus:
		        print('%s at %s' % (errorStatus.prettyPrint(),
		                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
		    else:
		    	# TODO handle wrapping when counter32/counter64 overflows
		    	# A switch can have hundreds of interfaces... blows away custom metrics
		    	#interface = self._calculate_interface_split(varBinds)
		    	#interfaces.append(interface)
		    	self._populate_interface_metrics(varBinds, metrics)

		#for interface in interfaces:
			#for name,value in interface.items():
				#print('{} - {}'.format(name,value))

		for key,value in metrics.items():
			print(key)
			print(*value, sep=' ')

	def _calculate_interface_split(self,varBinds):
		interface = {}
		interface['bandwidth'] = varBinds[0][1]
		interface['incoming_traffic'] = varBinds[1][1]
		interface['outgoing_traffic'] = varBinds[2][1]
		interface['incoming_errors'] = varBinds[3][1]
		interface['outgoing_errors'] = varBinds[4][1]
		interface['incoming_discards'] = varBinds[5][1]
		interface['outgoing_discards'] = varBinds[6][1]
		# Unicast + Broadcast + Multicast
		interface['incoming_packets'] = float(varBinds[6][1]) + float(varBinds[7][1]) + float(varBinds[8][1])
		interface['outgoing_packets'] = float(varBinds[9][1]) + float(varBinds[10][1]) + float(varBinds[11][1])

		return interface

	def _populate_interface_metrics(self,varBinds, metrics):
		metrics.setdefault('bandwidth', []).append(varBinds[0][1])
		metrics.setdefault('incoming_traffic', []).append(varBinds[1][1])
		metrics.setdefault('outgoing_traffic', []).append(varBinds[2][1])
		metrics.setdefault('incoming_errors', []).append(varBinds[3][1])
		metrics.setdefault('outgoing_errors', []).append(varBinds[4][1])
		metrics.setdefault('incoming_discards', []).append(varBinds[5][1])
		metrics.setdefault('outgoing_discards', []).append(varBinds[6][1])
		metrics.setdefault('incoming_ucast', []).append(varBinds[7][1])
		metrics.setdefault('outgoing_ucast', []).append(varBinds[8][1])
		metrics.setdefault('incoming_bcast', []).append(varBinds[9][1])
		metrics.setdefault('outgoing_bcast', []).append(varBinds[10][1])
		metrics.setdefault('incoming_mcast', []).append(varBinds[11][1])
		metrics.setdefault('outgoing_mcast', []).append(varBinds[12][1])


