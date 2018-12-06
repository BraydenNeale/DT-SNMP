import random
import json
import logging
import requests
import re
import socket
import _thread
import time
from requests.auth import HTTPBasicAuth

# TODO work out how to bundle local module
#from snmp.host_resource_mib import HostResourceMIB
#from snmp.if_mib import IFMIB
from pysnmp.hlapi import *

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

        if_mib = IFMIB(device, authentication)
        if_metrics = if_mib.poll_metrics()

        # Dimensions pull back too many custom metrics...
        # I could restrict to known disks e.g. /, /var... 
        # ...or a user option to hit all disks + interfaces
        #e1.absolute(key = metric['name'], value = split['result'], dimensions = split['dimensions'])

        _log_values(logger, host_metrics, if_metrics)
        # Host resource Mib are all utilisation %s
        for key,value in host_metrics.items():
            e1.absolute(key=key, value=value)

        # IF-Mib are all counter values
        for key,value in if_metrics.items():
            e1.relative(key=key, value=value)

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

def _log_values(logger, host_metrics, if_metrics):
    for key,value in host_metrics.items():
        logger.info('{} - {}'.format(key,value))
    for key,value in if_metrics.items():
        logger.info('{} - {}'.format(key,value))

#####           #####
# CLASS IMPORTS
#####           #####
class HostResourceMIB():
    """
    Metric processing for Host-Resouce-Mib
    Host infrastructure statistics

    This is supported by most device types 

    Reference
    http://www.net-snmp.org/docs/mibs/host.html

    Usage
    hr_mib = HostResourceMIB(device, authentication)
    host_metrics = hr_mib.poll_metrics()

    Returns a dictionary containing values for:
    cpu, memory, disk

    TODO implement disk splits
    """

    mib_name = 'HOST-RESOURCES-MIB'

    def __init__(self, device, authentication):
        self.poller = Poller(device, authentication)

    def poll_metrics(self):
        cpu = self._poll_cpu()
        memory, disk = self._poll_storage()

        metrics = {
            'cpu': cpu,
            'memory': memory,
            #'disk': disk,
        }

        return metrics

    def _poll_cpu(self):
        cpu_metrics = [
            'hrProcessorLoad',
        ]
        oids = [(self.mib_name, metric) for metric in cpu_metrics]
        gen = self.poller.snmp_connect_bulk(oids)
        return self._process_cpu(gen)

    def _process_cpu(self,gen):
        count = 0
        total = 0
        for item in gen:
            errorIndication, errorStatus, errorIndex, varBinds = item
            if errorIndication:
                print(errorIndication)
            elif errorStatus:
                print('%s at %s' % (errorStatus.prettyPrint(),
                                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
            else:
                # 1 index per iteration
                for name, value in varBinds:
                    count += 1
                    total += value

        return (total / float(count))

    def _poll_storage(self):
        storage_metrics = [
            'hrStorageDescr',
            'hrStorageSize',
            'hrStorageUsed',
        ]
        oids = [(self.mib_name, metric) for metric in storage_metrics]
        gen = self.poller.snmp_connect_bulk(oids)

        return self._process_storage(gen)

    def _process_storage(self,gen):
        storage = []
        memory_name = 'Physical memory'
        memory = 0
        for item in gen:
            errorIndication, errorStatus, errorIndex, varBinds = item
            if errorIndication:
                print(errorIndication)
            elif errorStatus:
                print('%s at %s' % (errorStatus.prettyPrint(),
                                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
            else:
                index = {}
                index['descriptor'] = varBinds[0][1].prettyPrint()
                size = varBinds[1][1]
                used = varBinds[2][1]
                index['utilisation'] = (used / float(size))*100

                if index['descriptor'] == memory_name:
                    memory = index['utilisation']
                    # TODO handle disk splitting
                    break
                else:   
                    storage.append(index)
        
        return memory, storage

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

class Poller():
    """
    snmp.Poller
    This module wraps the pysnmp APIs to connect to a device

    Usage
    poller = new Poller
    gen = self.poller.snmp_connect_bulk(self.oids)

    You can then iterate through the generator:
    for item in gen:
        errorIndication, errorStatus, errorIndex, varBinds = item
    """
    
    auth_protocols = {
        'md5': usmHMACMD5AuthProtocol,
        'sha': usmHMACSHAAuthProtocol,
        'sha224': usmHMAC128SHA224AuthProtocol,
        'sha256': usmHMAC192SHA256AuthProtocol,
        'sha384': usmHMAC256SHA384AuthProtocol,
        'sha512': usmHMAC384SHA512AuthProtocol,
        'noauth': usmNoAuthProtocol
    }

    priv_protocols = {
        'des': usmDESPrivProtocol,
        '3des': usm3DESEDEPrivProtocol,
        'aes': usmAesCfb128Protocol,
        'aes192': usmAesCfb192Protocol,
        'aes256': usmAesCfb256Protocol,
        'nopriv': usmNoPrivProtocol
    }

    def __init__(self, device, authentication):
        self.authentication = authentication
        self.device = device
        self._build_auth_object()

    def snmp_connect(self, oid):
        """
        Only use for old SNMP agents
        Prefer snmp_connect_bulk in all cases
        Send an snmp get request
        """
        gen = getCmd(
            SnmpEngine(),
            self.auth_object,
            UdpTransportTarget((self.device['host'], self.device['port'])),
            ContextData(),
            ObjectType(ObjectIdentity(oid)))
        return next(gen)

    def snmp_connect_bulk(self, oids):
        """
        Optimised get - supported with SNMPv2C
        Send a single getbulk request
        Supported inputs:
        String - e.g. 1.3.6.1.2.1.31.1.1.1
        Tuple - e.g. (IF-MIB, ifSpeed)
        List of Tuple - e.g. ([(IF-MIB,ifSpeed), (HOST-RESOURCES-MIB,cpu)])

        Recommended to only call with lists of OIDs from the same table
        Otherwise you can end up polling for End of MIB.
        """
        non_repeaters = 0
        max_repetitions = 25

        if (isinstance(oids, str)):
            oid_object = [ObjectType(ObjectIdentity(oids))]
        elif (isinstance(oids, tuple)):
            oid_object = [ObjectType(ObjectIdentity(*oids))]
        elif(isinstance(oids, list)): # List of Tuple
            oid_object = [ObjectType(ObjectIdentity(*oid)) for oid in oids]

        gen = bulkCmd(
            SnmpEngine(),
            self.auth_object,
            UdpTransportTarget((self.device['host'], self.device['port'])),
            ContextData(),
            non_repeaters,
            max_repetitions,             
            *oid_object,
            lexicographicMode=False)

        return gen

    def _build_auth_object(self):
        authentication = self.authentication
        if (authentication['version'] == 3):
            self.auth_object = UsmUserData(
                authentication['user'],
                authentication['auth']['key'],
                authentication['priv']['key'],
                self.auth_protocols.get(authentication['auth']['protocol'], None),
                self.priv_protocols.get(authentication['priv']['protocol'], None))
        elif(authentication['version'] == 2):
            self.auth_object = CommunityData(authentication['user'], mpModel=1)
        elif(authentication['version'] == 1):
            self.auth_object = CommunityData(authentication['user'], mpModel=0)




