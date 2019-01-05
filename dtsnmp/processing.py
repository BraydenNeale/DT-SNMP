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

        metrics = {}
        index = 0
        for item in gen:
            index += 1
            errorIndication, errorStatus, errorIndex, varBinds = item

            if errorIndication:
                logger.error(errorIndication)
                # Return early or we could be stuck timing out hitting each index
                # TODO handle this more gracefully
                return metrics
            elif errorStatus:
                logger.error('%s at %s' % (errorStatus.prettyPrint(),
                                    errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                # Return early or we could be stuck timing out hitting each index
                # TODO handle this more gracefully
                return metrics
            else:
                processor(index=str(index), varBinds=varBinds, metrics=metrics)

        return metrics

"""
Display in the same format as snmpwalk.
Ripped straight from http://snmplabs.com/pysnmp/quick-start.html
"""
def mib_print(index, varBinds, metrics):
    for varBind in varBinds:
        print(' = '.join([x.prettyPrint() for x in varBind]))

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
			average_dict['dimension'] = None
			total = 0

			for metric in metrics:
				total += metric['value']
				is_absolute = metric['is_absolute_number']

			average_dict['is_absolute_number'] = is_absolute
			average_dict['value'] = total / count
			average_metrics.setdefault(endpoint, []).append(average_dict)

	return average_metrics