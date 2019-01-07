import logging
from .poller import Poller
from .processing import process_metrics, reduce_average, split_oid_index

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
	incoming_traffic, outgoing_traffic, incoming_errors,
	outgoing_errors, incoming_discards, outgoing_discards,
	incoming_packets, outgoing_packets
	"""
	
	mib_name = 'IF-MIB'
	mib_metrics = [
	'ifSpeed', # Bandwidth
	'ifHCInOctets', # Incoming Traffic
	'ifHCOutOctets', # Outgoing Traffic,
	'ifInErrors',
	'ifOutErrors',
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
		return process_metrics(gen, calculate_interface_metrics)

"""
Processing Function to be used with processing.process_metrics
Extracts the following for each interface
ifSpeed -> varBinds[0] (ignored)
ifHCInOctets -> varBinds[1]
ifHCOutOctets -> varBinds[2]
ifInErrors -> varBinds[3]
ifOutErrors -> varBinds[4]
ifInDiscards -> varBinds[5]
ifOutDiscards -> varBinds[6]
ifHCInUcastPkts -> varBinds[7]
ifHCInBroadcastPkts -> varBinds[8]
ifHCInMulticastPkts -> varBinds[9]
ifHCOutUcastPkts -> varBinds[10]
ifHCOutBroadcastPkts -> varBinds[11]
ifHCOutMulticastPkts -> varBinds[12]
"""
def calculate_interface_metrics(varBinds, metrics):
	#bandwidth = {'value': float(varBinds[0][1])}
	index = split_oid_index(varBinds[0][0])
	incoming_traffic = {'value': float(varBinds[1][1])}
	outgoing_traffic = {'value': float(varBinds[2][1])}
	incoming_errors = {'value': float(varBinds[3][1])}
	outgoing_errors = {'value': float(varBinds[4][1])}
	incoming_discards = {'value': float(varBinds[5][1])}
	outgoing_discards = {'value': float(varBinds[6][1])}
	# Unicast + Broadcast + Multicast
	total_incoming = float(varBinds[7][1]) + float(varBinds[8][1]) + float(varBinds[9][1])
	total_outgoing = float(varBinds[10][1]) + float(varBinds[11][1]) + float(varBinds[12][1])
	incoming_packets = {'value': total_incoming}
	outgoing_packets = {'value': total_outgoing}

	# All metrics are relative
	# Calculate per interface... so same dimension for each
	dict_list = [incoming_traffic, outgoing_traffic, incoming_errors, outgoing_errors, incoming_discards, outgoing_discards, incoming_packets, outgoing_packets]
	for metric_dict in dict_list:
		metric_dict['is_absolute_number'] = False
		metric_dict['dimension'] = {'Interface': index}

	# Add this interface to our list so far
	metrics.setdefault('incoming_traffic', []).append(incoming_traffic)
	metrics.setdefault('outgoing_traffic', []).append(outgoing_traffic)
	metrics.setdefault('incoming_errors', []).append(incoming_errors)
	metrics.setdefault('outgoing_errors', []).append(outgoing_errors)
	metrics.setdefault('incoming_discards', []).append(incoming_discards)
	metrics.setdefault('outgoing_discards', []).append(outgoing_discards)
	metrics.setdefault('incoming_packets', []).append(incoming_packets)
	metrics.setdefault('outgoing_packets', []).append(outgoing_packets)

