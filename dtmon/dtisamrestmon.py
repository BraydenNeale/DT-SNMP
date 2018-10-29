from .dtmonitoringrest import DTRestMonitoring
import requests, time, datetime, sched, random
import re
import ast
import logging
import base64
import json
import threading

class DTISAMRestMon(DTRestMonitoring):
    propDetails  = [
        {"properyName" : "JVM - Up time", "type": "jvm", "key":"UpTime"}
    ]	

    jvmDetails = [
        { "timeseriesId" : "custom:custom_package.rest.jvm.cpu.time", "dimensions":{}, "displayName" : "JVM - CPU Time", "unit" : "Millisecond", "key" : 'ProcessCPU', "display": "metrics"},
        { "timeseriesId" : "custom:custom_package.rest.jvm.memory.used", "dimensions":{}, "displayName" : "JVM - Memory Used", "unit" : "Kibibyte", "key" : 'UsedMemory', "display": "metrics"},
        { "timeseriesId" : "custom:custom_package.rest.jvm.memory.free", "dimensions":{}, "displayName" : "JVM - Memory Free", "unit" : "Kibibyte", "key" : 'FreeMemory', "display": "metrics"},
        { "timeseriesId" : "custom:custom_package.rest.jvm.gc.time", "dimensions":{}, "displayName" : "JVM - GC Time", "unit" : "Millisecond", "key" : 'GcTime', "display": "metrics"},
        { "timeseriesId" : "custom:custom_package.rest.jvm.gc.count", "dimensions":{}, "displayName" : "JVM - GC Count", "unit" : "Count", "key" : 'GcCount', "display": "metrics"},
        { "timeseriesId" : "custom:custom_package.rest.jvm.uptime", "dimensions":{}, "displayName" : "JVM - Up Time", "unit" : "Millisecond", "key" : 'UpTime', "display": "props"},
    ]

    threadDetails = [
        { "timeseriesId" : "custom:custom_package.rest.thread.active", "dimensions":{}, "displayName" : "Thread - Active", "unit" : "Count", "key" : 'ActiveThreads', "display": "metrics"},
        { "timeseriesId" : "custom:custom_package.rest.thread.pool", "dimensions":{}, "displayName" : "Thread - Pool", "unit" : "Count", "key" : 'PoolSize', "display": "metrics"},
    ]

    configDB = [
        { "timeseriesId" : "custom:custom_package.rest.db.config.managedconnection.count", "dimensions":{}, "displayName" : "Config DB - Managed Connection Count", "unit" : "Count", "key" : 'ManagedConnectionCount', "display": "metrics"},
    ]

    hvDB = [
        { "timeseriesId" : "custom:custom_package.rest.db.hv.managedconnection.count", "dimensions":{}, "displayName" : "HVDB - Managed Connection Count", "unit" : "Count", "key" : 'ManagedConnectionCount', "display": "metrics"},
    ]

    timeOutCount = [
        { "timeseriesId" : "custom:custom_package.rest.timeout", "dimensions":{}, "displayName" : "TimeOut - Count", "unit" : "Count", "key" : '', "display": "metrics"}
    ]

    def __init__(
            self,
            dtEndpoint,
            deviceAuth,
            deviceDisplay,
            timeout={"dtserver": 10, "device": 10},
            logDetails={"level": "error",
                        "location": "./DTISAMRest.log"},
            timeQueryInSec=None):
        super(DTISAMRestMon, self).__init__(dtEndpoint, deviceAuth,
                                             deviceDisplay, timeout=timeout, logDetails=logDetails)
        self._replacePropertyValue("timeseriesId", "custom_package", "com.ibm.isam", self.threadDetails)
        logging.debug('metrics after package formatted %s', self.threadDetails)
        self._replacePropertyValue("timeseriesId", "custom_package", "icom.ibm.isam", self.configDB)
        logging.debug('metrics after package formatted %s', self.configDB)
        self._replacePropertyValue("timeseriesId", "custom_package", "com.ibm.isam", self.hvDB)
        logging.debug('metrics after package formatted %s', self.hvDB)

    def dtrun(self):
        t1 = threading.Thread(target=self.__runThread)
        t1.start()
        t1.join()



    def __runThread(self):
        res = self.__getIsamRestMetrics("threads")
        metrics = []
        if(res is not None):
            self.__processPointMetrics(res, self.threadDetails)
            outArr = self.__registerAndBuildSeriesArray(self.threadDetails)
            metrics = metrics + outArr
        res = self.__getIsamRestMetrics("config")
        if(res is not None):
            self.__processPointMetrics(res, self.configDB)
            outArr = self.__registerAndBuildSeriesArray(self.configDB)
            metrics = metrics + outArr
        res = self.__getIsamRestMetrics("hvdb")
        if(res is not None):
            self.__processPointMetrics(res, self.hvDB)
            outArr = self.__registerAndBuildSeriesArray(self.hvDB)
            metrics = metrics + outArr
        
        self.deviceDisplay["series"] = metrics
        self._sendMetricData(self.deviceDisplay["id"], json=self.deviceDisplay)

    def __getIsamRestMetrics(self, metricType):        
        res = self.makeRequest("GET", "/monitor/"  + metricType, json={})
        #fail
        if(res is None):
            logging.error("Nothing to process")
            return
        if(not res.status_code == requests.codes.ok):
            logging.error("request return code %d", res.status_code)
            return
        #successful
        resDict = json.loads(res.text)
        return resDict
   
    def __processPointMetrics(self, resDict, collection):
        for item in collection:
            item["dataPoints"] = [[ int(time.time() * 1000) , resDict[item["key"]]]]
      

    def __registerAndBuildSeriesArray(self, metrics):
        outArr = []
        for metric in metrics:
            data = {"displayName": metric["displayName"], "unit": metric["unit"], "dimensions": [], "types": [self.deviceDisplay["type"]]}
            logging.debug('metric data: %s', data)
            self._registerDTMetric(metric['timeseriesId'], json=data)
            outArr.append({"timeseriesId": metric["timeseriesId"], "dimensions": {}, "dataPoints": metric["dataPoints"]})
        return outArr