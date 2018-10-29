from .dtmonitoringrest import DTRestMonitoring
import requests, time, datetime, sched, random
import re
import ast
import logging
import base64
import json
import threading

class DTDPowerESMon(DTRestMonitoring):

    metrics = [
        { "timeseriesId" : "custom:custom_package.rest.ttlrsp", "dimensions": [], "displayName" : "Total Response Time", "unit" : "Millisecond", 
            "match": {"single_key": "ttlrsp_avg"}
        },
        { "timeseriesId" : "custom:custom_package.rest.cncrsp", "dimensions": [], "displayName" : "Concrete Response Time", "unit" : "Millisecond", 
            "match": {"single_key": "cncrsp_avg"}
        },
        { "timeseriesId" : "custom:custom_package.rest.count.total", "dimensions": [], "displayName" : "Total Requests", "unit" : "Count",
            "match": {"single_key": "doc_count"}
        },
        { "timeseriesId" : "custom:custom_package.rest.count.success", "dimensions": [], "displayName" : "Success Count", "unit" : "Count",
            "match": {"nested_key": "status_count.buckets", "key": "key", "is": "SUCCESS"}
        },
        { "timeseriesId" : "custom:custom_package.rest.count.error", "dimensions": ["type"], "displayName" : "Error Count", "unit" : "Count", 
            "match": {"nested_key": "status_count.buckets", "key": "key", "not": "SUCCESS", "dimension": "key"}
        }
    ]

    timeQueryInSec = {
        "shiftBy": 0, 
        "interval": 60
    }
    shiftByMinute = 0
    systemPrefix, indexPrefix = "", ""

    def __init__(
            self,
            dtEndpoint,
            deviceAuth,
            indexPrefix,
            systemPrefix,
            deviceDisplay,
            timeout={"dtserver": 10, "device": 10},
            logDetails={"level": "error",
                        "location": "/tmp/DTDPowerESMon.log"},
            timeQueryInSec=None):
        super(DTDPowerESMon, self).__init__(dtEndpoint, deviceAuth,
                                             deviceDisplay, timeout=timeout, logDetails=logDetails)
        if timeQueryInSec is not None:
            self.timeQueryInSec = timeQueryInSec 
        self.__replacePackageName()
        self.indexPrefix = indexPrefix
        self.systemPrefix = systemPrefix
        logging.debug('metrics after package formatted %s', self.metrics)

    def dtrun(self):
        t1 = threading.Thread(target=self.__runThread)
        t1.start()
        t1.join()

    def __runThread(self):
        timeQueryInSec = self.__buildTimeQuery()
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": {
                        "prefix": {"server": self.systemPrefix}
                    },
                    "filter": {
                        "range" : {
                            "@timestamp" : {
                                "gte" : timeQueryInSec["gte"],
                                "lt": timeQueryInSec["lt"]
                            }
                        }
                    }
                }
            },
            "aggs":{
                "server": { 
                    "terms": {
                        "field": "server.keyword"
                    },
                    "aggs": {
                        "ttlrsp_avg": {
                            "avg": {"field": "ttlrsp"}
                        },
                        "cncrsp_avg": {
                            "avg": {"field": "cncrsp"}
                        },
                        "status_count": {
                            "terms": {
                                "field": "result.keyword"
                            },
                            "aggs":{
                                "count": {"value_count": {"field": "result.keyword"}}
                            }
                        }
                    }
                }
            }
        }
        logging.debug("query: %s", query)

        res = self.makeRequest("POST", "/" + self.indexPrefix + "*/_search", json=query)
        devices = self.__processESResp(res)
        logging.debug("devices: \n%s", devices)
        self.__registerMetrics()
        for device in devices:
            self._sendMetricData(device["id"], json=device["details"])

    def __processESResp(self, res):
        devices = []
        #fail
        if(res is None):
            logging.error("Nothing to process")
            return
        if(not res.status_code == requests.codes.ok):
            logging.error("request return code %d", res.status_code)
            return
        #successful
        resDict = json.loads(res.text)
        dpowers = resDict["aggregations"]["server"]["buckets"]
        logging.debug("Data Powers: \n%s", dpowers)
        for dp in dpowers:
            id = dp["key"]
            nameMatch = re.match('(' + self.systemPrefix + ')(\w+)(prd|prod|vnd)(\w*)\.(\d+)', id)
            name = ('%s %s %s %s %s' % (nameMatch.group(1).title(), nameMatch.group(2).title(), nameMatch.group(3).title(), nameMatch.group(4).title(), nameMatch.group(5).title()))
            device = {
                "displayName": name, 
                "type": self.deviceDisplay["type"], 
                "tags": self.deviceDisplay["tags"], 
                "properties": {},
                "favicon" : self.deviceDisplay["favicon"],
                "series": self.__buildSeriesForDevice(dp)
            }
            devices.append({"id": id, "details": device})
        return devices

    def __buildSeriesForDevice(self, device):
        series = []
        for m in self.metrics:
            result = None
            toMatch = m["match"]
            if("single_key" in toMatch):
                result = self._findByKey(device, toMatch["single_key"])
                if(toMatch["single_key"] == "ttlrsp_avg" or toMatch["single_key"] == "cncrsp_avg"):
                    serie = {"timeseriesId": m["timeseriesId"], "dimensions": {}, "dataPoints": [[ int(time.time() * 1000), float(result[0][1]["value"])]]}
                elif(toMatch["single_key"] == "doc_count"):
                    serie = {"timeseriesId": m["timeseriesId"], "dimensions": {}, "dataPoints": [[ int(time.time() * 1000), float(result[0][1])]]}
                series.append(serie)
            elif("nested_key" in toMatch):
                nestedKeys = toMatch["nested_key"].split(".")
                toMatchAgainst = self._getNestedValue(device, nestedKeys)
                if("is" in toMatch):
                    result = self._findByKey(toMatchAgainst, toMatch["key"], toMatch["is"])
                    if(toMatch["is"]=="SUCCESS"):
                        serie = {"timeseriesId": m["timeseriesId"], "dimensions": {}, "dataPoints": [[ int(time.time() * 1000), float(result[0]["doc_count"])]]}
                        series.append(serie)
                if("not" in toMatch):
                    result = self._findByKey(toMatchAgainst, toMatch["key"], toMatch["not"], match=False)
                    if(toMatch["not"]=="SUCCESS"):
                        for r in result:
                            serie = {"timeseriesId": m["timeseriesId"], "dimensions": {"type": r["key"]}, "dataPoints": [[ int(time.time() * 1000), float(r["doc_count"])]]}
                            series.append(serie)
        return series

    def __registerMetrics(self):
        for metric in self.metrics:
            data = {"displayName": metric["displayName"], "unit": metric["unit"], "dimensions": metric["dimensions"], "types": [self.deviceDisplay["type"]]}
            logging.debug('metric data: %s', data)
            self._registerDTMetric(metric['timeseriesId'], json=data)

    def __replacePackageName(self):
        packageName = self.deviceDisplay["type"].lower().replace(" ", ".")
        for item in self.metrics:
            item["timeseriesId"] = item["timeseriesId"].replace("custom_package", packageName)

    def __buildTimeQuery(self):
        gte = ("now-%ds" % (self.timeQueryInSec["shiftBy"] + self.timeQueryInSec["interval"]))
        lt = ("now-%ds" % (self.timeQueryInSec["shiftBy"]))
        return {"gte": gte, "lt": lt}
