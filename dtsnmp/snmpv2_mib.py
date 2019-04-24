import logging
from .poller import Poller
from .processing import convert_to_readable_time

logger = logging.getLogger(__name__)

class SNMPv2MIB():
	"""
	Properties from SNMPv2MIB
	This is also used as a device connectivity check

	Reference
	http://www.oidview.com/mibs/0/SNMPv2-MIB.html

	Usage
	snmpv2_mib = SNMPv2MIB(device, authentication)
	property_dict = snmpv2_mib.poll_properties()

	Returns system property values
	"""

	def __init__(self, device, authentication):
		self.poller = Poller(device, authentication)

	def poll_properties(self):
		mib_properties = [
			'1.3.6.1.2.1.1.1',	# 'sysDescr',
			'1.3.6.1.2.1.1.2',	# 'sysObjectID',
			'1.3.6.1.2.1.1.3',	# 'sysUpTime',
			'1.3.6.1.2.1.1.4',	# 'sysContact',
			'1.3.6.1.2.1.1.5', 	# 'sysName',
			'1.3.6.1.2.1.1.6',	# 'sysLocation',
			'1.3.6.1.2.1.1.7',	# 'sysServices',
			'1.3.6.1.2.1.1.8'	# 'sysORLastChange'
		]
		timeout = 2
		retries = 1
		gen = self.poller.snmp_connect_bulk(mib_properties, timeout, retries)
		props = {}
		errorIndication, errorStatus, errorIndex, varBinds = next(gen)
		if errorIndication:
		    raise Exception(errorIndication)
		elif errorStatus:
		    raise Exception('%s at %s' % (errorStatus.prettyPrint(),
		                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
		else:
		    get_system_properties(varBinds, props)

		return props

"""
sysDescr -> varBinds[0]
sysObjectID -> varBinds[1]
sysUpTime -> varBinds[2]
sysContact -> varBinds[3]
sysName -> varBinds[4]
sysLocation -> varBinds[5]
sysServices -> varBinds[6]
sysORLastChange -> varBinds[7]
"""
def get_system_properties(varBinds, props):
	props['sysDescr'] = str(varBinds[0][1])
	props['sysObjectID'] = str(varBinds[1][1])
	props['sysUpTime'] = convert_to_readable_time(str(varBinds[2][1]))
	props['sysContact'] = str(varBinds[3][1])
	props['sysName'] = str(varBinds[4][1])
	props['sysLocation'] = str(varBinds[5][1])
	props['sysServices'] = str(varBinds[6][1])
	props['sysORLastChange'] = convert_to_readable_time(str(varBinds[7][1]))
