import json
import logging
from queue import Queue
from threading import Thread
from pprint import pprint
from dtsnmp.host_resource_mib import HostResourceMIB
from dtsnmp.if_mib import IFMIB
from dtsnmp.cisco_process_mib import CiscoProcessMIB
from dtsnmp.snmpv2_mib import SNMPv2MIB
from dtsnmp.f5_bigip_system_mib import F5BigIPSystemMIB

"""
Test script designed to match the flow of custom_snmp_base_plugin_remote.py
Used to test snmp classes without requiring a build/package of the extension
Usage python test.py
"""
def test_query():
    with open('properties.json') as fp:
        config = json.load(fp)

    device = _validate_device(config)
    authentication = _validate_authentication(config)

    # Connection check and system properties
    snmpv2_mib = SNMPv2MIB(device, authentication)
    property_dict = {}
    try:
        property_dict = snmpv2_mib.poll_properties()
    except Exception as e:
        # Just report the pysnmp exception back to the end user
        info = 'Device connection issue: check snmp access'
        raise Exception('{} - {}'.format(info,str(e))) from e

    _display_properties(property_dict)

    metric_queue = Queue()
    thread_list = []
    mib_list = []

    # VENDOR/DEVICE SPECIFIC POLLING
    DEVICE_OBJECT_ID = property_dict['sysObjectID']
    F5_OBJECT_ID = '1.3.6.1.4.1.3375'
    CISCO_OBJECT_ID = '1.3.6.1.4.1.9'

    if DEVICE_OBJECT_ID.startswith(CISCO_OBJECT_ID):
        print('CISCO')
    elif DEVICE_OBJECT_ID.startswith(F5_OBJECT_ID):
        print('F5')
    else:
        print('OTHER')

    hr_mib = HostResourceMIB(device, authentication)
    mib_list.append(hr_mib)
    if_mib = IFMIB(device, authentication)
    mib_list.append(if_mib)
    cisco_mib = CiscoProcessMIB(device, authentication)
    mib_list.append(cisco_mib)
    f5_mib = F5BigIPSystemMIB(device, authentication)
    mib_list.append(f5_mib)

    for mib in mib_list:
        t = Thread(target=lambda q,mib: q.put(mib.poll_metrics()), args=([metric_queue, mib]))
        t.start()
        thread_list.append(t)

    for t in thread_list:
        t.join()

    _display_metrics(metric_queue)

def _display_metrics(metric_queue):
    while not metric_queue.empty():
        #pprint(metric_queue.get())
        for endpoint,metrics in metric_queue.get().items():
            for metric in metrics:
                print('Key = {}, Value = {}, Absolute? = {}, Dimension = {}'.format(endpoint, metric['value'], metric['is_absolute_number'], metric['dimension']))

def _display_properties(property_dict):
    for key,value in property_dict.items():
        print('key = {}, Value = {}'.format(key,value))

def _validate_device(config):
    hostname = config.get('hostname')
    group_name = config.get('group')
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
        'port': int(port)
    }

    return device

def _validate_authentication(config):
    snmp_version = config.get('snmp_version')
    snmp_user = config.get('snmp_user')
    auth_protocol = config.get('auth_protocol', None)
    auth_key = config.get('auth_key', None)
    priv_protocol = config.get('priv_protocol', None)
    priv_key = config.get('priv_key', None)

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

if __name__ == '__main__':
    logging.basicConfig(filename='test.log',level=logging.DEBUG)
    test_query()