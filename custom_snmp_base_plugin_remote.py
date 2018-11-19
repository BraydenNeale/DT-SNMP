import random
import json
import logging
import requests
import re
import socket
import _thread
import time
from requests.auth import HTTPBasicAuth

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

        device = _validate_device(config)
        authentication = _validate_authentication(config)
        _log_inputs(logger, device, authentication)

        # Create the group/device entities in Dynatrace
        g1_name = '{0} - {1}'.format(device['type'], device['group'])
        g1 = self.topology_builder.create_group(g1_name, g1_name)
        e1_name = '{0} - {1}'.format(device['type'], device['host'])
        e1 = g1.create_element(e1_name, e1_name)
        
        hr_mib = HostResourceMIB(device, authentication)
        host_metrics = hr_mib.poll_metrics()

        # TODO
        # if_mib = IFMIB(device, authentication)
        # if_metrics = if_mib.poll_metrics()

        # Test Plugin
        data = {}
        data['cpu_utilisation'] = host_metrics['cpu']
        data['memory_utilisation'] = host_metrics['memory']
        data['disk_utilisation'] = random.randint(0,101)
        data['incoming_traffic'] = random.randint(0,100001)
        data['outgoing_traffic'] = random.randint(0,100001)
        data['inbound_error_rate'] = random.randint(0,101)
        data['outbound_error_rate'] = random.randint(0,101)
        data['inbound_loss_rate'] = random.randint(0,101)
        data['outbound_loss_rate'] = random.randint(0,101)

        # TODO handle dimensions - see official extension code
        #e1.absolute(key = metric['name'], value = split['result'], dimensions = split['dimensions'])

        for key,value in data.items():
            e1.absolute(key=key, value=value)

# Helper methods
def _validate_device(config):
    hostname = config['hostname']
    group_name = config['group']
    device_type = config['type']

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
    snmp_version = config['snmp_version']
    snmp_user = config['snmp_user']
    auth_protocol = config['auth_protocol']
    auth_key = config['auth_key']
    priv_protocol = config['priv_protocol']
    priv_key = config['priv_key']

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
    for key,value in device:
        logger.info('{} - {}'.format(key,value))
    for key,value in authentication:
        logger.info('{} - {}'.format(key,value))