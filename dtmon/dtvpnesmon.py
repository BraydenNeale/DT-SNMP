from .dtmonitoringrest import DTRestMonitoring
import requests, time, datetime, sched, random
import re
import ast
import logging
import base64
import json
import threading

class DTVPNESMon(DTRestMonitoring):

    metrics = [
        { "timeseriesId" : "custom:domain.vpn.rest.uniqueuser.count.vpngroup", "dimensions": ["vpngroup"], "displayName" : "Number of Unique Users By VPN Group", "unit" : "Count"},
        { "timeseriesId" : "custom:domain.vpn.rest.uniqueuser.count.region", "dimensions": ["region"], "displayName" : "Number of Unique Users By Region", "unit" : "Count"},
    ]

    timeQueryInSec = {
        "shiftBy": 0, 
        "interval": 270
    }
    shiftByMinute = 0
    systemPrefix, indexPrefix = "", ""

    def __init__(
            self,
            dtEndpoint,
            deviceAuth,
            indexPrefix,
            deviceDisplay,
            timeout={"dtserver": 10, "device": 10},
            logDetails={"level": "error",
                        "location": "/tmp/DTVPNESMon.log"},
            timeQueryInSec=None):
        super(DTVPNESMon, self).__init__(dtEndpoint, deviceAuth,
                                             deviceDisplay, timeout=timeout, logDetails=logDetails)
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
        uniq_user_query = {
            "size": 0,
            "query": {
                "range" : {
                    "@timestamp" : {
                        "gte" : timeQueryInSec["gte"],
                        "lt": timeQueryInSec["lt"]
                    }
                }     
            },
            "aggs":{
                "vpngroup":{
                    "terms": {
                        "field": "vpn_group.keyword",
                        "size": 10
                    },
                    "aggs": {
                        "uniq_user" : {
                            "cardinality": { 
                                "script": "doc['vpn_user.keyword'].value + '-' + doc['vpn_isp_ip_address'].value" 
                            }
                        }
                    }
                }
                ,
                "region":{
                    "terms": {
                        "field": "geoip.region_name.keyword",
                        "size": 10
                    },
                    "aggs": {
                        "uniq_user" : {
                            "cardinality": { 
                                "script": "doc['vpn_user.keyword'].value + '-' + doc['vpn_isp_ip_address'].value" 
                            }
                        }
                    }
                }
            }
        }
        logging.debug("query: %s", uniq_user_query)

        res = self.makeRequest("POST", "/" + self.indexPrefix + "*/_search", json=uniq_user_query)
        series = self.__buildUniqueUserSeries(res)
        self.deviceDisplay["series"] = series
        logging.debug("devices: \n%s", self.deviceDisplay)
        self.__registerMetrics()
        self._sendMetricData(self.deviceDisplay["id"], json=self.deviceDisplay)
          


    def __buildUniqueUserSeries(self, res):
        #fail
        if(res is None):
            logging.error("Nothing to process")
            return
        if(not res.status_code == requests.codes.ok):
            logging.error("request return code %d", res.status_code)
            return

        series = []    
        resDict = json.loads(res.text)

        currentTime = int(time.time() * 1000)
        uniqueUserVPNMetric = self._findByKey(self.metrics, "displayName", "Number of Unique Users By VPN Group")
        vpngroup = resDict["aggregations"]["vpngroup"]["buckets"]
        vpntotal = 0
        for item in vpngroup:
            series.append({"timeseriesId": uniqueUserVPNMetric[0]["timeseriesId"], "dimensions": {"vpngroup": item["key"]}, "dataPoints": [[ currentTime, item["uniq_user"]["value"]]]})
            vpntotal += item["uniq_user"]["value"]

        uniqueUserRegionMetric = self._findByKey(self.metrics, "displayName", "Number of Unique Users By Region") 
        region = resDict["aggregations"]["region"]["buckets"]
        regiontotal = 0  
        for item in region: 
            series.append({"timeseriesId": uniqueUserRegionMetric[0]["timeseriesId"], "dimensions": {"region": item["key"]}, "dataPoints": [[ currentTime, item["uniq_user"]["value"]]]}) 
            regiontotal += item["uniq_user"]["value"]
        series.append({"timeseriesId": uniqueUserRegionMetric[0]["timeseriesId"], "dimensions": {"region": "Others"}, "dataPoints": [[ currentTime, vpntotal-regiontotal]]}) 
        return series

        #logging.debug("Number Uniq User: \n%s", numUniqUsers)
        #uniqueUserMetric = self._findByKey(self.metrics, "displayName", "Number of Unique Users")
        #series.append({"timeseriesId": uniqueUserMetric[0]["timeseriesId"], "dimensions": {}, "dataPoints": [[ int(time.time() * 1000), numUniqUsers]]})
        #return series

    def __registerMetrics(self):
        for metric in self.metrics:
            data = {"displayName": metric["displayName"], "unit": metric["unit"], "dimensions": metric["dimensions"], "types": [self.deviceDisplay["type"]]}
            logging.debug('metric data: %s', data)
            self._registerDTMetric(metric['timeseriesId'], json=data)


    def __buildTimeQuery(self):
        gte = ("now-%ds" % (self.timeQueryInSec["shiftBy"] + self.timeQueryInSec["interval"]))
        lt = ("now-%ds" % (self.timeQueryInSec["shiftBy"]))
        return {"gte": gte, "lt": lt}
