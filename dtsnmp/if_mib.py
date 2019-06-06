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
	http://www.oidview.com/mibs/0/IF-MIB.html
	http://cric.grenoble.cnrs.fr/Administrateurs/Outils/MIBS/?oid=1.3.6.1.2.1.31.1.1.1

	May need to refine which counters based on device bps
	https://www.cisco.com/c/en/us/support/docs/ip/simple-network-management-protocol-snmp/26007-faq-snmpcounter.html
	
	Usage
	if_mib = IFMIB(device, authentication)
	if_metrics = if_mib.poll_metrics()

	Returns a dictionary containing values for:
	incoming_traffic, outgoing_traffic, incoming_errors,
	outgoing_errors, incoming_discards, outgoing_discards,
	incoming_packets, outgoing_packets
	"""

	def __init__(self, device, authentication):
		self.poller = Poller(device, authentication)

	def poll_metrics(self):
		if_metrics = [
			'1.3.6.1.2.1.2.2.1.2',		# 'ifDescr',
			'1.3.6.1.2.1.31.1.1.1.6',	# 'ifHCInOctets' = Incoming Traffic
			'1.3.6.1.2.1.31.1.1.1.10',	# 'ifHCOutOctets' = Outgoing Traffic,
			'1.3.6.1.2.1.2.2.1.14', 	# 'ifInErrors',
			'1.3.6.1.2.1.2.2.1.20',		# 'ifOutErrors',
			'1.3.6.1.2.1.2.2.1.13', 	# 'ifInDiscards',
			'1.3.6.1.2.1.2.2.1.19',		# 'ifOutDiscards',
			'1.3.6.1.2.1.31.1.1.1.7', 	# 'ifHCInUcastPkts',
			'1.3.6.1.2.1.31.1.1.1.9', 	# 'ifHCInBroadcastPkts',
			'1.3.6.1.2.1.31.1.1.1.8', 	# 'ifHCInMulticastPkts',
			'1.3.6.1.2.1.31.1.1.1.11', 	# 'ifHCOutUcastPkts',
			'1.3.6.1.2.1.31.1.1.1.13', 	# 'ifHCOutBroadcastPkts',
			'1.3.6.1.2.1.31.1.1.1.12' 	# 'ifHCOutMulticastPkts'
		]
		gen = self.poller.snmp_connect_bulk(if_metrics)
		return process_metrics(gen, calculate_interface_metrics)

"""
Processing Function to be used with processing.process_metrics
Extracts the following for each interface
ifDescr -> varBinds[0]
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
	index = str(varBinds[0][1])

	# Temp Hot Fix - issue #3
	incoming_errors = {'value': 0}
	outgoing_errors = {'value': 0}
	incoming_discards = {'value': 0}
	outgoing_discards = {'value': 0}
	incoming_traffic = {'value': 0}
	outgoing_traffic = {'value': 0}
	total_incoming = 0
	total_outgoing = 0

	try:
			incoming_errors['value'] = float(varBinds[3][1])
			outgoing_errors['value'] = float(varBinds[4][1])
			incoming_discards['value'] = float(varBinds[5][1])
			outgoing_discards['value'] = float(varBinds[6][1])
			incoming_traffic['value'] = float(varBinds[1][1])
			outgoing_traffic['value'] = float(varBinds[2][1])
			# Unicast + Broadcast + Multicast
			total_incoming = float(varBinds[7][1]) + float(varBinds[8][1]) + float(varBinds[9][1])
			total_outgoing = float(varBinds[10][1]) + float(varBinds[11][1]) + float(varBinds[12][1])
	except ValueError as e:
			logger.info('IF-MIB {}: No more variables left in this MIB View'.format(index))
	
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

