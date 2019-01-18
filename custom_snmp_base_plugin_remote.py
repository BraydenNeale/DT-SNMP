import logging
from queue import Queue
from threading import Thread

from dtsnmp.host_resource_mib import HostResourceMIB
from dtsnmp.if_mib import IFMIB
from dtsnmp.snmpv2_mib import SNMPv2MIB

import ruxit.api.selectors
from ruxit.api.base_plugin import RemoteBasePlugin
from ruxit.api.data import PluginMeasurement, PluginProperty, MEAttribute
from ruxit.api.exceptions import AuthException, ConfigException, NothingToReportException
from ruxit.api.events import Event, EventMetadata

logger = logging.getLogger(__name__)

class CustomSnmpBasePluginRemote(RemoteBasePlugin):
    def query(self, **kwargs):
        config = kwargs['config']      
        debug_logging = config['debug']
        if debug_logging:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.WARNING)

        # Ensure our inputs are valid
        device = _validate_device(config)
        authentication = _validate_authentication(config)
        _log_inputs(logger, device, authentication)

        # Connection check and system properties
        snmpv2_mib = SNMPv2MIB(device, authentication)
        property_dict = {}
        try:
            property_dict = snmpv2_mib.poll_properties()
        except Exception as e:
            # Just report the pysnmp exception back to the end user
            info = 'Device connection issue: check snmp access'
            raise AuthException('{}: {}'.format(info,str(e)))

        # Create the group/device entities in Dynatrace
        g1_name = '{0} - {1}'.format(device['type'], device['group'])
        g1 = self.topology_builder.create_group(g1_name, g1_name)
        e1_name = '{0} - {1}'.format(device['type'], device['host'])
        e1 = g1.create_element(e1_name, e1_name)
        
        # Poll for snmp metrics
        metric_queue = Queue()
        thread_list = []
        mib_list = []

        # Host Resource MIB
        hr_mib = HostResourceMIB(device, authentication)
        mib_list.append(hr_mib)

        # IF MIB
        if_mib = IFMIB(device, authentication)
        mib_list.append(if_mib)

        for mib in mib_list:
            # Lambda function - so that the thread can write poll_metrics() into the queue
            t = Thread(target=lambda q,mib: q.put(mib.poll_metrics()), args=([metric_queue, mib]))
            t.start()
            thread_list.append(t)
        for t in thread_list:
            t.join()

        # Keep track of the custom metrics consumed
        custom_metrics = 0
        # Send metrics and dimensions through to DT
        while not metric_queue.empty():
            for endpoint,metrics in metric_queue.get().items():
                for metric in metrics:
                    if metric['is_absolute_number']:
                        e1.absolute(key=endpoint, value=metric['value'], dimensions=metric['dimension'])
                    else:
                        e1.relative(key=endpoint, value=metric['value'], dimensions=metric['dimension'])

                    custom_metrics += 1
                    logger.info('Key = {}, Value = {}, Absolute? = {}, Dimension = {}'.format(endpoint, metric['value'], metric['is_absolute_number'], metric['dimension']))

        if custom_metrics == 0:
            raise NothingToReportException('Connected: But no metrics were returned when polling {}:{}'.format(device['host'], device['port']))

        property_dict['Custom metrics'] = str(custom_metrics)
        for key,value in property_dict.items():
            e1.report_property(key, value)

# Helper methods
def _validate_device(config):
    hostname = config.get('hostname')
    group = config.get('group')
    device_type = config.get('device_type')

    # Check inputs are valid...
    if not hostname:
        raise ConfigException('Hostname must not be empty')

    if not group:
        raise ConfigException('Group must not be empty')

    if not device_type:
        raise ConfigException('Device Type must not be empty')

    # Default SNMP port
    port = 161
    host = hostname
    # If entered as 127.0.0.1:1234, extract the ip and the port
    split_host = hostname.split(':')
    if len(split_host) > 1:
        host = split_host[0]
        port = split_host[1]

    try:
        port = int(port)
    except ValueError:
        raise ConfigException('Invalid port \'{}\' in hostname input: {}'.format(port, hostname))

    device = {
        'host': host,
        'port': port,
        'type': device_type,
        'group': group
    }

    return device

def _validate_authentication(config):
    snmp_version = config.get('snmp_version')
    snmp_user = config.get('snmp_user')
    auth_protocol = config.get('auth_protocol')
    auth_key = config.get('auth_key')
    priv_protocol = config.get('priv_protocol')
    priv_key = config.get('priv_key')

    # Check inputs are valid...
    if not snmp_version:
        raise ConfigException('SNMP Version must not be empty')

    if not snmp_user:
        raise ConfigException('SNMP User (v3) or Community String (v2) must not be empty')

    # Other values can be None...
    # V2
        # Expected and ignored
    # V3
        # Match SNMP security level
        # No Auth or Priv = noAuthNoPriv
        # Auth no Priv = authNoPriv
        # Auth + Priv = authPriv

    try:
        snmp_version = int(snmp_version)
    except ValueError:
        raise ConfigException('Expected a number for SNMP Version, received \'{}\''.format(snmp_version))

    if snmp_version == 1:
        raise ConfigException('SNMP Version 1 not yet? supported')
    elif not (snmp_version == 2 or snmp_version == 3):
        raise ConfigException('SNMP Version expected to be 2 or 3, received \'{}\''.format(snmp_version))

    # TODO If auth or priv protocols don't match expected inputs...
    if auth_protocol:
        auth_protocol = auth_protocol.lower()
    if priv_protocol:
        priv_protocol = priv_protocol.lower()

    authentication = {
        'version': snmp_version,
        'user': snmp_user,
        'auth': {
            'protocol': auth_protocol,
            'key': auth_key
        },
        'priv': {
            'protocol': priv_protocol,
            'key': priv_key
        }
    }

    return authentication
    
def _log_inputs(logger, device, authentication):
    for key,value in device.items():
        logger.info('{} - {}'.format(key,value))
    for key,value in authentication.items():
        logger.info('{} - {}'.format(key,value))