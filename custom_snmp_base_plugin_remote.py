import logging
from queue import Queue
from threading import Thread

from snmp.host_resource_mib import HostResourceMIB
from snmp.if_mib import IFMIB

import ruxit.api.selectors
from ruxit.api.base_plugin import RemoteBasePlugin
from ruxit.api.data import PluginMeasurement, PluginProperty, MEAttribute
from ruxit.api.exceptions import AuthException, ConfigException
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

        # Create the group/device entities in Dynatrace
        g1_name = '{0} - {1}'.format(device['type'], device['group'])
        g1 = self.topology_builder.create_group(g1_name, g1_name)
        e1_name = '{0} - {1}'.format(device['type'], device['host'])
        e1 = g1.create_element(e1_name, e1_name)
        
        # Poll for snmp metrics
        metric_queue = Queue()
        thread_list = []
        mib_list = []

        # Host Resource MIB - TODO Disk filtering
        hr_mib = HostResourceMIB(device, authentication)
        mib_list.append(hr_mib)

        # IF MIB - TODO Interface filtering
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

        e1.report_property('Custom metrics', str(custom_metrics))

# Helper methods
def _validate_device(config):
    hostname = config.get('hostname')
    group = config.get('group')
    device_type = config.get('device_type')

    # Default port
    port = 161
    # If entered as 127.0.0.1:1234, extract the ip and the port
    split_host = hostname.split(':')
    if len(split_host) > 1:
        hostname = split_host[0]
        port = split_host[1]

    # Check inputs are valid...

    device = {
        'host': hostname,
        'port': int(port),
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

    authentication = {
        'version': int(snmp_version),
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