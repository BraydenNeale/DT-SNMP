from .dtmonitoringrest import DTRestMonitoring
import requests, time, datetime, sched, random
import re
import ast
import logging
import base64
import json
import threading

class DTUbserAgentESMon(DTRestMonitoring):

    metrics = [
        { "timeseriesId" : "custom:<DOMAIN>.uberagent.rest.peakdevicesonline.count", "dimensions": ["site"], "displayName" : "Peak Devices Online", "unit" : "Count"},
        { "timeseriesId" : "custom:<DOMAIN>.uberagent.rest.totalappcrash.count", "dimensions": ["site"], "displayName" : "Total App Crash", "unit" : "Count"},
        { "timeseriesId" : "custom:<DOMAIN>.uberagent.rest.totalapphang.count", "dimensions": ["site"], "displayName" : "Total App Hang", "unit" : "Count"},
        { "timeseriesId" : "custom:<DOMAIN>.uberagent.rest.averagelogontime.ms", "dimensions": ["site"], "displayName" : "Average Logon Time", "unit" : "MilliSecond"},
        { "timeseriesId" : "custom:<DOMAIN>.uberagent.rest.averagewaittime.ms", "dimensions": ["site"], "displayName" : "Average Wait Time", "unit" : "MilliSecond"}
    ]

    timeQueryInSec = {
        "shiftBy": 0, 
        "interval": 300
    }
    shiftByMinute = 0
    systemPrefix, indexPrefix = "", ""
    sites = []

    def __init__(
            self,
            dtEndpoint,
            deviceAuth,
            indexPrefix,
            deviceDisplay,
            timeout={"dtserver": 10, "device": 10},
            logDetails={"level": "error",
                        "location": "/tmp/DTUberESMon.log"},
            timeQueryInSec=None,
            sites=[]):
        super(DTUbserAgentESMon, self).__init__(dtEndpoint, deviceAuth,
                                             deviceDisplay, timeout=timeout, logDetails=logDetails)

        self.sites = sites                                     
        if timeQueryInSec is not None:
            self.timeQueryInSec = timeQueryInSec 
        self.indexPrefix = indexPrefix
        #self.systemPrefix = systemPrefix
        logging.debug('metrics after package formatted %s', self.metrics)

    def dtrun(self):
        t1 = threading.Thread(target=self.__runThread)
        t1.start()
        t1.join()

    def __runThread(self):
        timeQueryInSec = self.__buildTimeQuery()
        site_metrics = {
            "size": 0,
            "query": {
                "bool": {
                    "must": {
                        "terms": {
                            "AdSite": self.sites
                        }
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
                "site": {
                    "terms": {
                        "field": "AdSite"
                    },
                    "aggs": {
                        "error_status": {
                            "terms": {
                                "script": "doc['ErrorType'].value + '-' + doc['Sourcetype'].value",
                                "size": 100
                            }
                        },
                        "peakdevicesonline": {
                            "cardinality": {
                                "field": "host"
                            }
                        },
                        "average":{
                            "terms": {
                                "field": "Sourcetype",
                                "size": 100
                            },
                            "aggs": {
                                "logonMs": {
                                    "avg": {
                                        "field": "TotalLogonTimeMs"
                                    }
                                },
                                "UIDelayMs":{
                                    "avg": {
                                        "field": "UIDelayMs"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        logging.debug("query: %s", site_metrics)

        res = self.makeRequest("POST", "/" + self.indexPrefix + "*/_search", json=site_metrics)
        series = self.__buildSiteMetrics(res)
        
        self.deviceDisplay["series"] = series
        logging.debug("devices: \n%s", self.deviceDisplay)
        self.__registerMetrics()
        self._sendMetricData(self.deviceDisplay["id"], json=self.deviceDisplay)
          


    def __buildSiteMetrics(self, res):
        #fail
        if(res is None):
            logging.error("Nothing to process")
            return
        if(not res.status_code == requests.codes.ok):
            logging.error("request return code %d", res.status_code)
            return

        series = []    
        resDict = json.loads(res.text)
        #print(resDict)
        sites = resDict["aggregations"]["site"]["buckets"]
        for site in sites:
            currentTime = int(time.time() * 1000)
            #Total Devices
            totalDevicesCountMetric = self._findByKey(self.metrics, "displayName", "Peak Devices Online")
            series.append({"timeseriesId": totalDevicesCountMetric[0]["timeseriesId"], "dimensions": {totalDevicesCountMetric[0]["dimensions"][0]: site["key"]}, "dataPoints": [[ currentTime, site["peakdevicesonline"]["value"]]]})
            #total App Crash
            totalAppCrashMetric = self._findByKey(self.metrics, "displayName", "Total App Crash")
            totalAppCrashCount = self._findByKey(site["error_status"]["buckets"], "key", "1-uberAgent:Application:Errors")
            totalAppCrashCount = totalAppCrashCount[0]["doc_count"] if len(totalAppCrashCount) > 0 else 0
            series.append({"timeseriesId": totalAppCrashMetric[0]["timeseriesId"], "dimensions": {totalAppCrashMetric[0]["dimensions"][0]: site["key"]}, "dataPoints": [[ currentTime, totalAppCrashCount]]})
            #total App Hangs
            totalAppHangMetric = self._findByKey(self.metrics, "displayName", "Total App Hang")
            totalAppHangCount = self._findByKey(site["error_status"]["buckets"], "key", "2-uberAgent:Application:Errors")
            totalAppHangCount = totalAppHangCount[0]["doc_count"] if len(totalAppHangCount) > 0 else 0
            series.append({"timeseriesId": totalAppHangMetric[0]["timeseriesId"], "dimensions": {totalAppHangMetric[0]["dimensions"][0]: site["key"]}, "dataPoints": [[ currentTime, totalAppHangCount]]})

            #average
            averageMs = site["average"]["buckets"]

            #avg logon time
            avgLogonMetric = self._findByKey(self.metrics, "displayName", "Average Logon Time")
            averageLogonTime = self._findByKey(averageMs, "key", "uberAgent:Logon:TotalLogonTimeMs")
            averageLogonTime = averageLogonTime[0]["logonMs"]["value"] if len(averageLogonTime) > 0 else 0
            series.append({"timeseriesId": avgLogonMetric[0]["timeseriesId"], "dimensions": {avgLogonMetric[0]["dimensions"][0]: site["key"]}, "dataPoints": [[ currentTime, averageLogonTime]]})
            
            #avg ui delay time
            avgWaitTimeMetric = self._findByKey(self.metrics, "displayName", "Average Wait Time")
            averageWaitTime = self._findByKey(averageMs, "key", "uberAgent:Application:UIDelay")
            averageWaitTime = averageWaitTime[0]["UIDelayMs"]["value"] if len(averageWaitTime) > 0 else 0
            series.append({"timeseriesId": avgWaitTimeMetric[0]["timeseriesId"], "dimensions": {avgWaitTimeMetric[0]["dimensions"][0]: site["key"]}, "dataPoints": [[ currentTime, averageWaitTime]]})

        return series

    def __registerMetrics(self):
        for metric in self.metrics:
            data = {"displayName": metric["displayName"], "unit": metric["unit"], "dimensions": metric["dimensions"], "types": [self.deviceDisplay["type"]]}
            logging.debug('metric data: %s', data)
            self._registerDTMetric(metric['timeseriesId'], json=data)


    def __buildTimeQuery(self):
        gte = ("now-%ds" % (self.timeQueryInSec["shiftBy"] + self.timeQueryInSec["interval"]))
        lt = ("now-%ds" % (self.timeQueryInSec["shiftBy"]))
        return {"gte": gte, "lt": lt}
