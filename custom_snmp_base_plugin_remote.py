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

        # Host resource Mib are all utilisation %s
        for key,value in host_metrics.items():
            e1.absolute(key=key, value=value)

        # IF-Mib are all counter values
        for key,value in if_metrics.items():
            e1.relative(key=key, value=value)

# Helper methods
def _validate_device(config):
    hostname = config.get('hostname')
    group_name = config.get('group')
    device_type = config.get('type')

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
    for key,value in device:
        logger.info('{} - {}'.format(key,value))
    for key,value in authentication:
        logger.info('{} - {}'.format(key,value))

# EXTERNAL CLASSES
class HostResourceMIB():
  poller = None

  mib_name = 'HOST-RESOURCES-MIB'

  def __init__(self, device, authentication):
    self.poller = Poller(device, authentication)

  def poll_metrics(self):
    cpu = self._poll_cpu()
    memory, disk = self._poll_storage()

    metrics = {
      'cpu': cpu,
      'memory': memory,
      'disk': disk,
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
  poller = None
  oids = None

  mib_name = 'IF-MIB'
  mib_metrics = [
      'ifInOctets', # Incoming Traffic
      'ifHCOutOctets', # Outgoing Traffic,
      'ifInErrors', # Incoming errors
      'ifOutErrors', # Outgoing errors
      'ifInDiscards', # Incoming loss rate
      'ifOutDiscards', # Outgoing loss rate
      'ifInUcastPkts',
      'ifOutUcastPkts',
  ]

  def __init__(self, device, authentication):
    self.poller = Poller(device, authentication)
    self.oids = [(self.mib_name, metric) for metric in self.mib_metrics]

  def poll_metrics(self):
    gen = self.poller.snmp_connect_bulk(self.oids)
    self._process_result(gen)

  def _process_result(self,gen):
    for item in gen:
        errorIndication, errorStatus, errorIndex, varBinds = item
        
        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                                errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                print(' = '.join([x.prettyPrint() for x in varBind]))

class Poller():
    device = {}
    authentication = {}
    auth_object = None

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
        gen = getCmd(
            SnmpEngine(),
            self.auth_object,
            UdpTransportTarget((self.device['host'], self.device['port'])),
            ContextData(),
            ObjectType(ObjectIdentity(oid)))
        return next(gen)

    def snmp_connect_bulk(self, oids):
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