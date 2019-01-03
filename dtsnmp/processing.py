import logging

logger = logging.getLogger(__name__)

""" 
Processing functions
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

def mib_print(index, varBinds, metrics):
    for varBind in varBinds:
        print(' = '.join([x.prettyPrint() for x in varBind]))

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