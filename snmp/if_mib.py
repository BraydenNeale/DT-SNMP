import logging
from .poller import Poller

logger = logging.getLogger(__name__)

class IFMIB():
	"""
	Metric processing for IF-MIB
	Interface network statistics 

	This is supported by most device types

	Reference
	http://www.net-snmp.org/docs/mibs/interfaces.html
	http://cric.grenoble.cnrs.fr/Administrateurs/Outils/MIBS/?oid=1.3.6.1.2.1.31.1.1.1

	Usage
	if_mib = IFMIB(device, authentication)
	if_metrics = if_mib.poll_metrics()

	Returns a dictionary containing values for:
	incoming_traffic, outgoing_traffic, inbound_error_rate,
	outbound_error_rate, inbound_loss_rate, outbound_loss_rate
	"""
	
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

	def __init__(self, device, authentication):
		self.poller = Poller(device, authentication)
		self.oids = [(self.mib_name, metric) for metric in self.mib_metrics]

	def poll_metrics(self):
		gen = self.poller.snmp_connect_bulk(self.oids)
		return self._process_result(gen)

	def _process_result(self,gen):
		interfaces = []
		index = 0
		for item in gen:
			index += 1
			errorIndication, errorStatus, errorIndex, varBinds = item

			if errorIndication:
			    logger.error(errorIndication)
			elif errorStatus:
			    logger.error('%s at %s' % (errorStatus.prettyPrint(),
			                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
			else:
				interface = self._calculate_interface_split(varBinds)
				interface['index'] = str(index)
				interfaces.append(interface)

		return interfaces

	# A switch can have hundreds of interfaces... can blow away custom metrics
	# Usage
	#interfaces = []
    #interface = self._calculate_interface_split(varBinds)
	#interfaces.append(interface)
	def _calculate_interface_split(self,varBinds):
		interface = {}
		#interface['bandwidth'] = varBinds[0][1]
		interface['incoming_traffic'] = varBinds[1][1]
		interface['outgoing_traffic'] = varBinds[2][1]
		interface['incoming_errors'] = varBinds[3][1]
		interface['outgoing_errors'] = varBinds[4][1]
		interface['incoming_discards'] = varBinds[5][1]
		interface['outgoing_discards'] = varBinds[6][1]
		# Unicast + Broadcast + Multicast
		interface['incoming_packets'] = int(varBinds[6][1]) + int(varBinds[7][1]) + int(varBinds[8][1])
		interface['outgoing_packets'] = int(varBinds[9][1]) + int(varBinds[10][1]) + int(varBinds[11][1])

		return interface



