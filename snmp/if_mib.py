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
		metrics = {}
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
				self._calculate_interface_metrics(str(index), varBinds, metrics)

		return metrics

	def _calculate_interface_metrics(self, index, varBinds, metrics):
		# Ignore bandwidth
		incoming_traffic = {'value': float(varBinds[1][1])}
		outgoing_traffic = {'value': float(varBinds[2][1])}
		incoming_errors = {'value': float(varBinds[3][1])}
		outgoing_errors = {'value': float(varBinds[4][1])}
		incoming_discards = {'value': float(varBinds[5][1])}
		outgoing_discards = {'value': float(varBinds[6][1])}
		# Unicast + Broadcast + Multicast
		total_incoming = float(varBinds[6][1]) + float(varBinds[7][1]) + float(varBinds[8][1])
		total_outgoing = float(varBinds[9][1]) + float(varBinds[10][1]) + float(varBinds[11][1])
		incoming_packets = {'value': total_incoming}
		outgoing_packets = {'value': total_outgoing}

		# All metrics are relative
		# Calculate per interface... so same dimension for each
		dict_list = [incoming_traffic, outgoing_traffic, incoming_errors, outgoing_errors, incoming_discards, outgoing_discards, incoming_packets, outgoing_packets]
		for metric_dict in dict_list:
			metric_dict['number_type'] = 'relative'
			metric_dict['dimension'] = {'Storage': index}

		# Add this interface to our list so far
		metrics.setdefault('incoming_traffic', []).append(incoming_traffic)
		metrics.setdefault('outgoing_traffic', []).append(outgoing_traffic)
		metrics.setdefault('incoming_errors', []).append(incoming_errors)
		metrics.setdefault('outgoing_errors', []).append(outgoing_errors)
		metrics.setdefault('incoming_discards', []).append(incoming_discards)
		metrics.setdefault('outgoing_discards', []).append(outgoing_discards)
		metrics.setdefault('incoming_packets', []).append(incoming_packets)
		metrics.setdefault('outgoing_packets', []).append(outgoing_packets)

