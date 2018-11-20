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
		return self._process_result(gen)

	def _process_result(self,gen):
		data = {}
		for item in gen:
		    errorIndication, errorStatus, errorIndex, varBinds = item
		    
		    if errorIndication:
		        print(errorIndication)
		    elif errorStatus:
		        print('%s at %s' % (errorStatus.prettyPrint(),
		                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
		    else:
		    	# TODO handle wrapping when counter32/counter64 overflows
		    	self._populate_interface_metrics(varBinds, data)

		return self._reduce_interface_metrics(data)

	# A switch can have hundreds of interfaces... blows away custom metrics
	# Usage
	#interfaces = []
    #interface = self._calculate_interface_split(varBinds)
	#interfaces.append(interface)
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

	def _populate_interface_metrics(self,varBinds, data):
		data.setdefault('bandwidth', []).append(varBinds[0][1])
		data.setdefault('incoming_traffic', []).append(varBinds[1][1])
		data.setdefault('outgoing_traffic', []).append(varBinds[2][1])
		data.setdefault('incoming_errors', []).append(varBinds[3][1])
		data.setdefault('outgoing_errors', []).append(varBinds[4][1])
		data.setdefault('incoming_discards', []).append(varBinds[5][1])
		data.setdefault('outgoing_discards', []).append(varBinds[6][1])
		data.setdefault('incoming_ucast', []).append(varBinds[7][1])
		data.setdefault('outgoing_ucast', []).append(varBinds[8][1])
		data.setdefault('incoming_bcast', []).append(varBinds[9][1])
		data.setdefault('outgoing_bcast', []).append(varBinds[10][1])
		data.setdefault('incoming_mcast', []).append(varBinds[11][1])
		data.setdefault('outgoing_mcast', []).append(varBinds[12][1])

	def _reduce_interface_metrics(self, data):
		# Bandwidth is an interface property...
		# Sum traffic across all interfaces
		incoming_traffic = sum(data['incoming_traffic'])
		outgoing_traffic = sum(data['outgoing_traffic'])

		incoming_errors = sum(data['incoming_errors'])
		outgoing_errors = sum(data['outgoing_errors'])
		incoming_discards = sum(data['incoming_discards'])
		outgoing_discards = sum(data['outgoing_discards'])
		incoming_ucast = sum(data['incoming_ucast'])
		outgoing_ucast = sum(data['outgoing_ucast'])
		incoming_bcast = sum(data['incoming_bcast'])
		outgoing_bcast = sum(data['outgoing_bcast'])
		incoming_mcast = sum(data['incoming_mcast'])
		outgoing_mcast = sum(data['outgoing_mcast'])

		incoming_packets = sum([incoming_ucast, incoming_bcast, incoming_mcast])
		outgoing_packets = sum([outgoing_ucast, outgoing_bcast, outgoing_mcast])

		# Error rate as defined in original script
		inbound_error_rate = (incoming_errors / incoming_packets)*100
		outbound_error_rate = (outgoing_errors / outgoing_packets)*100

		# Loss rate as defined in original script
		inbound_loss_rate = (incoming_discards / incoming_packets)*100
		outbound_loss_rate = (outgoing_discards / outgoing_packets)*100

		metrics = {
			'incoming_traffic': incoming_traffic,
			'outgoing_traffic': outgoing_traffic,
			'inbound_error_rate': inbound_error_rate,
			'outbound_error_rate': outbound_error_rate,
			'inbound_loss_rate': inbound_loss_rate,
			'outbound_loss_rate': outbound_loss_rate
		}

		return metrics




