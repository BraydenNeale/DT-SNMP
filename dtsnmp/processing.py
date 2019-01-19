import logging

logger = logging.getLogger(__name__)

""" 
General processing and helper functions
"""

"""
Build a metric dictionary from an snmp connection generator
Args:
    Gen - A generator returned from Poller.snmp_connect_bulk
    Processor - a procesing function for each index (default is to just print)
        index - The current iteration through the generator
        varBinds - The variable bindings from snmpget on an object descriptor - name,value
        metrics - The dictionary of metric endpoints to populate
"""
def process_metrics(gen, processor=None):
        if not processor:
            processor = mib_print

        # DT limits metric splits at 100, so stop processing after that
        DIMENSION_LIMIT = 100
        dimensions = 0
        metrics = {}

        for item in gen:
            dimensions += 1
            if dimensions > DIMENSION_LIMIT:
                break

            errorIndication, errorStatus, errorIndex, varBinds = item

            if errorIndication:
                logger.error(errorIndication)
                break
            elif errorStatus:
                logger.error('%s at %s' % (errorStatus.prettyPrint(),
                                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                break
            else:
                processor(varBinds=varBinds, metrics=metrics)

        return metrics

"""
Display in the same format as snmpwalk.
Ripped straight from http://snmplabs.com/pysnmp/quick-start.html
"""
def mib_print(varBinds, metrics):
    for varBind in varBinds:
        print(' = '.join([x.prettyPrint() for x in varBind]))

"""
Display in a debug format so that we can understand and map the Varbinds
"""
def debug_print(varBinds, metrics):
    for iteration, (key, value) in enumerate(varBinds):
        #oid = key.prettyPrint().split('.')[-1]
        oid = key
        print('iteration={}, oid={}: value={}'.format(iteration, oid, value))

"""
Reducer function to manage custom_metric overload.
Takes a metric dictionary and averages the metrics under each endpoint
Dimensions are then ignored and set to None
TODO - take the reducer as an arg to support sum, count, median...
"""
def reduce_average(metric_dict):
    average_metrics = {}
    for endpoint,metrics in metric_dict.items():
        count = len(metrics)
        if count > 0:
            average_dict = {}
            average_dimension = None
            is_absolute = False
            total = 0

            for metric in metrics:
                total += metric['value']
                is_absolute = metric['is_absolute_number']
                average_dimension = metric['dimension']

            average_dict['is_absolute_number'] = is_absolute
            average_dict['value'] = total / count
            # Same dimension key... but value is now just 'average'
            average_dict['dimension'] = average_dimension.fromkeys(average_dimension, 'Average')
            average_metrics.setdefault(endpoint, []).append(average_dict)

    return average_metrics

"""
Split the index out from the rest of the OID
IF-MIB::ifHCInOctets.1 -> 1
1.3.6.1.2.1.31.1.1.1.6.1 -> 1
IF-MIB::ifHCInOctets.2 -> 2
"""
def split_oid_index(oid):
    return oid.prettyPrint().split('.')[-1]