from poller import Poller

def test_poller():
    device = {
        "host":"demo.snmplabs.com",
        "port": 161
    }

    authentication = {
        "version": 2,
        "user": "public",
        "auth": {
            "protocol": None,
            "key": None
        },
        "priv": {
            "protocol": None,
            "key": None
        }
    }

    hostmib_name = 'HOST-RESOURCES-MIB'
    hostmib_metrics = [
        'hrProcessorLoad', # CPU Utilisation
        'hrStorageType',
        'hrStorageDescr',
        'hrStorageSize',
        'hrStorageUsed',
    ]

    ifmib_name = 'IF-MIB'
    ifmib_metrics = [
        'ifInOctets', # Incoming Traffic
        'ifHCOutOctets', # Outgoing Traffic,
        'ifInErrors', # Incoming errors
        'ifOutErrors', # Outgoing errors
        'ifInDiscards', # Incoming loss rate
        'ifOutDiscards', # Outgoing loss rate
        'ifInUcastPkts',
        'ifOutUcastPkts',
    ]

    host_resource_oids = [(hostmib_name, metric) for metric in hostmib_metrics]
    if_oids = [(ifmib_name, metric) for metric in ifmib_metrics]

    poller = Poller(device, authentication)
    gen = poller.snmp_connect_bulk(host_resource_oids)
    process_poll_result(gen)
    gen = poller.snmp_connect_bulk(if_oids)
    process_poll_result(gen)

def process_poll_result(gen):
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

if __name__ == '__main__':
    test_poller()