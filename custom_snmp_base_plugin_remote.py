from dtmon.dtmonitoringsnmp import DTSNMPMonitoring

import json
import logging
import requests
import re
import socket
import _thread
import time
from requests.auth import HTTPBasicAuth

import ruxit.api.selectors
from ruxit.api.base_plugin import RemoteBasePlugin
from ruxit.api.data import PluginMeasurement, PluginProperty, MEAttribute
from ruxit.api.exceptions import AuthException, ConfigException
from ruxit.api.events import Event, EventMetadata

logger = logging.getLogger(__name__)

class CustomSnmpBasePluginRemote(RemoteBasePlugin):
    def query(self, **kwargs):
        config = kwargs["config"]
        host_name = config["host_name"]
        group_name = config["group"]
        device_type = config["device_type"]
        snmp_version = config["snmp_version"]
        snmp_user = config["snmp_user"]
        auth_protocol = config["auth_protocol"]
        auth_key = config["auth_key"]
        priv_protocol = config["priv_protocol"]
        priv_key = config["priv_key"]
        
        debug_logging = config["debug"]
        if debug_logging:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.WARNING)
        
        # Default port
        port = 161
        
        # If entered as 127.0.0.1:1234, extract the ip and the port
        split_host = host_name.split(":")
        if len(split_host) > 1:
            host_name = split_host[0]
            port = split_host[1]

        # Create the group/device entities in Dynatrace
        g1_name = "{0} - {1}".format(device_type, group_name)
        g1 = self.topology_builder.create_group(g1_name, g1_name)
        e1_name = "{0} - {1}".format(device_type - host_name)
        e1 = g1.create_element(e1_name, e1_name)
        
        # Poll the requested device for IF-MIB
            #cpu_utilisation, disk_utilisation, physical_memory_utilisation, virtual_memory_utilisation, other_memory_utilisation
        # Poll the requested device for Host-Resource-MIB
            #incoming_traffic, outgoing_traffic, inbound_error_rate, outbound_error_rate, inbound_loss_rate, outbound_loss_rate

        # TODO handle dimensions - see official extension code
        #e1.absolute(key = metric["name"], value = split["result"], dimensions = split["dimensions"])

        e1.absolute(key = "cpu_utilisation", value = cpu_utilisation)
        e1.absolute(key = "disk_utilisation", value = disk_utilisation)
        e1.absolute(key = "physical_memory_utilisation", value = physical_memory_utilisation)
        e1.absolute(key = "virtual_memory_utilisation", value = virtual_memory_utilisation)
        e1.absolute(key = "other_memory_utilisation", value = other_memory_utilisation)
        e1.absolute(key = "incoming_traffic", value = incoming_traffic)
        e1.absolute(key = "outgoing_traffic", value = outgoing_traffic)
        e1.absolute(key = "inbound_error_rate", value = inbound_error_rate)
        e1.absolute(key = "outbound_error_rate", value = outbound_error_rate)
        e1.absolute(key = "inbound_loss_rate", value = inbound_loss_rate)
        e1.absolute(key = "outbound_loss_rate", value = outbound_loss_rate)
    