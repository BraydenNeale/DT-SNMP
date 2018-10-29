import requests
import time
import datetime
import sched
import random
import re
import ast
import logging
from pymemcache.client import base
import threading
import json
import subprocess
import socket


class DTMonitoringBase(object):
    dtEndpoint, deviceAuth, deviceDisplay = {}, {}, {}
    logFormat = ""
    logDetails, timeout = {}, {}
    client = None
    threadLock = {}
    timeSeriesIdPrefix = ""

    def __init__(
            self,
            dtEndpoint,
            deviceAuth,
            deviceDisplay,
            timeout={"dtserver": 10, "device": 10},
            logDetails={"level": "error",
                        "location": "/tmp/DTMonitoring.log"},
            memcachedServer = {"use": True, "address": "localhost", "port": 11211},
            tsPrefix="<DOMAIN>.genericdevice",
            getLatency = False):
        self.timeout = timeout
        self.dtEndpoint = dtEndpoint
        self.deviceAuth = deviceAuth
        self.deviceDisplay = deviceDisplay
        self.logDetails = logDetails
        if(memcachedServer["use"]):
            self.client = base.Client((memcachedServer["address"], memcachedServer["port"]))
        self.threadLock = threading.Lock()
        self.__validateInput()
        self.logFormat = '%(asctime)-15s - %(levelname)s - %(message)s'
        logging.basicConfig(format=self.logFormat,
                            filename=self.logDetails["location"],
                            level=self.__getLogLevel())
        self.timeSeriesIdPrefix = "custom:" + tsPrefix
        if getLatency == True:
            t1 = threading.Thread(target=self._getLatency())
            t1.start()
            t1.join()                

    def __validateInput(self):
        if (not isinstance(self.dtEndpoint, dict)
                or not isinstance(self.deviceAuth, dict)
                or not isinstance(self.deviceDisplay, dict)
                or not isinstance(self.timeout, dict)
                or not isinstance(self.logDetails, dict)):
            raise TypeError('dtEndpoint, deviceAuth, deviceDisplay, timeout'
                            ' and logDetails should be of type dict')

        if (not "url" in self.dtEndpoint
            or self.dtEndpoint["url"].strip() == ""
            or not "apiToken" in self.dtEndpoint
                or self.dtEndpoint["apiToken"].strip() == ""):
            raise ValueError("url and apiToken of dtEndpoint"
                             " should not be empty")

        if (not "host" in self.deviceAuth
                or self.deviceAuth["host"].strip() == ""):
            raise ValueError("host should not be empty")

        if (not "dtserver" in self.timeout
            or not isinstance(self.timeout["dtserver"], int)
            or not "device" in self.timeout
                or not isinstance(self.timeout["device"], int)):
            raise ValueError("dtserver and device timeout"
                             " should be of type int")

        if (not "level" in self.logDetails
            or self.logDetails["level"].strip() == ""
            or not "location" in self.logDetails
                or self.logDetails["location"].strip() == ""):
            raise ValueError("level and location of log should not be empty")

        if (not "tags" in self.deviceDisplay
                or not isinstance(self.deviceDisplay["tags"], list)):
            self.deviceDisplay["tags"] = []

    def __getLogLevel(self):
        lowerCaseLevel = self.logDetails["level"].lower()
        if(lowerCaseLevel == "error"):
            return logging.ERROR
        elif(lowerCaseLevel == "warning"):
            return logging.WARNING
        elif(lowerCaseLevel == "info"):
            return logging.INFO
        elif(lowerCaseLevel == "debug"):
            return logging.DEBUG

    def _tickToString(self, tfield):
        ticks = int(tfield)
        seconds = ticks/100
        tfield = str(datetime.timedelta(seconds=seconds))
        return tfield

    def _registerDTMetric(self, tsId, json={}, verify=None, timeout=None):
        url = ('%s/api/v1/timeseries/%s?Api-Token=%s' % (
            self.dtEndpoint["url"], tsId, self.dtEndpoint["apiToken"]))
        logging.debug("Registering metric url: %s", url)
        r = self._makeRequest("put",
                              url,
                              json=json,
                              verify=verify,
                              timeout=timeout)
        logging.debug("Resp Code: %s - Text: %s", r.status_code, r.text)

    def _sendMetricData(self, deviceId, json={}, verify=None, timeout=None):
        url = ('%s/api/v1/entity/infrastructure/custom/%s?Api-Token=%s' % (
            self.dtEndpoint["url"], deviceId, self.dtEndpoint["apiToken"]))
        logging.debug("Sending metrics url: %s, data: %s", url, json)
        r = self._makeRequest("post",
                              url,
                              json=json,
                              verify=verify,
                              timeout=timeout)
        logging.debug("Resp Code: %s - Text: %s", r.status_code, r.text)                      

    def _makeRequest(self,
                     method,
                     url,
                     headers={},
                     json={},
                     verify=None,
                     timeout=None):
        _verify = False
        if verify is not None:
            _verify = verify
        _timeout = self.timeout["device"]
        if timeout is not None:
            _timeout = timeout
        try:
            if method.lower() == "get":
                return requests.get(
                    url,
                    json=json,
                    verify=_verify,
                    timeout=_timeout,
                    headers=headers)
            elif method.lower() == "post":
                return requests.post(
                    url,
                    json=json,
                    verify=_verify,
                    timeout=_timeout,
                    headers=headers)
            elif method.lower() == "put":
                return requests.put(
                    url,
                    json=json,
                    verify=_verify,
                    timeout=_timeout,
                    headers=headers)
            elif method.lower() == "delete":
                return requests.delete(
                    url,
                    json=json,
                    verify=_verify,
                    timeout=_timeout,
                    headers=headers)
        except requests.exceptions.Timeout:
            logging.error('Request to %s Timed Out, exceeding %d seconds',
                          url, _timeout)
        except requests.exceptions.RequestException as e:
            logging.error("Config: Request to %s has exception %s",
                          url, e)
        return None

    def _getNestedValue(self, dict, list):
        d = dict
        for item in list:
            d = d[item]
        return d

    """
    This method find dictionary elements in a collection based on the key.
    Parameters: 
      1. collection: a dictionary or a list of dictionary
      2. key: the key of the dictionary you want to find
      3. matchCondition: string value of the element[key] you want to find
      4. match: True or False. You can find match vs non-match value
    Return: a list of matching elements
    Eg:
    metricList = [
		{"suffix": "snmp.host.memoryutilisation.ram", 
			"details": { "displayName" : "Physical Memory Utilisation", "unit" : "Percent", "dimensions": [] }},
		{"suffix": "snmp.host.memoryutilisation.virtualmemory", 
			"details": { "displayName" : "Virtual Memory Utilisation", "unit" : "Percent", "dimensions": ["type"] }},
		{"suffix": "snmp.host.memoryutilisation.other", 
			"details": { "displayName" : "Other Memory Utilisation", "unit" : "Percent", "dimensions": ["type"] }}
	]
    idxs = self._findByKey(metricList, "suffix", "snmp.host.memoryutilisation.virtualmemory")
    print(idxs)
    >>>[{'suffix': 'snmp.host.memoryutilisation.virtualmemory', 'details': {'unit': 'Percent', 'displayName': 'Virtual Memory Utilisation', 'dimensions': ['type']}}]
    
    idxs = self._findByKey(metricList, "suffix", "snmp.host.memoryutilisation.virtualmemory", match=False)
    print(idxs)
    >>>[{'details': {'displayName': 'Physical Memory Utilisation', 'dimensions': [], 'unit': 'Percent'}, 'suffix': 'snmp.host.memoryutilisation.ram'}, 
    {'details': {'displayName': 'Other Memory Utilisation', 'dimensions': ['type'], 'unit': 'Percent'}, 'suffix': 'snmp.host.memoryutilisation.other'}]
    """
    def _findByKey(self, collection, key, matchCondition=None, match=True):
        result = None
        if(isinstance(collection, list)):
            result = filter(lambda x:
                            (x[key] == matchCondition) == match,
                            collection)
        elif(isinstance(collection, dict)):
            if(matchCondition is None):
                result = filter(lambda kv:
                                kv[0] == key,
                                collection.items())
            else:
                result = filter(lambda kv:
                                (kv[1] == matchCondition) == match,
                                collection.items())
        return list(result)

    #If Metric is the counter or keeps increasing since up time
    def _getCurrentMetric(self, mkey, thisPull, resetAt=None):
        if(self.client is None):
            raise ValueError("Cannot get current value because memcached is not on") 
        cachedKey = self.deviceDisplay["id"] + "." + mkey
        previousMetric = self.client.get(cachedKey)
        currentMetric = 0.0
        if previousMetric is not None:
            temp = thisPull - float(previousMetric)
            if temp < 0:
                if resetAt is not None:
                    currentMetric = temp + resetAt
                else:
                    currentMetric = float(previousMetric)
            else:
                currentMetric = float(temp)
        self.client.set(cachedKey, thisPull)
        return currentMetric


    def _replacePropertyValue(self, prop, toReplace, toReplaceWith, collection):
        if(isinstance(collection, list)):
            for item in collection:
                item[prop] = item[prop].replace(toReplace, toReplaceWith)
        elif(isinstance(collection, dict)):
            collection[prop] = collection[prop].replace(toReplace, toReplaceWith)

    def _sendMetricInBulk(self, series, bulkSize=100):
        collectionSize, start, end  = len(series), 0, 0
        while start < collectionSize:
            end = start + bulkSize
            logging.debug("collectionSize: %d, startPos: %d, endPos: %d" % (collectionSize, start, end))
            self.deviceDisplay["series"] = series[start:end]
            self._sendMetricData(self.deviceDisplay["id"], json=self.deviceDisplay)
            start = end

    def _getAndSetCachedJson(self, cachedKey, value, expire=60*10):
        if(self.client is None):
            raise ValueError("Cannot get current value because memcached is not on")
        retrievedData = None
        self.threadLock.acquire()
        retrievedBytes = self.client.get(cachedKey)
        if(retrievedBytes is not None):
            retrievedData = json.loads(retrievedBytes.decode('utf-8'))
        self.client.set(cachedKey, json.dumps(value), expire=expire)
        self.threadLock.release()
        return retrievedData

    def _setValueToCache(self, cachedKey, value, expire=60*10):
        if(self.client is None):
            raise ValueError("Cannot set value because memcached is not on") 
        self.threadLock.acquire()
        self.client.set(cachedKey, json.dumps(value), expire=expire)
        self.threadLock.release()

    def _getValueFromCache(self, cachedKey):
        if(self.client is None):
            raise ValueError("Cannot get value because memcached is not on") 
        retrievedData = None
        self.threadLock.acquire()
        retrievedBytes = self.client.get(cachedKey)
        if(retrievedBytes is not None):
            retrievedData = retrievedBytes.decode('utf-8')
        self.threadLock.release()
        return retrievedData

    def _getLatency(self):
        try:
            hostname = socket.gethostname()
            metric = {  "timeseriesId": ("%s%s%s" % (self.timeSeriesIdPrefix, ".ping.", "latency.pollinghost")),
                        "displayName" : ("Latency to requesting host (%s)"%(hostname)), 
                        "unit" : "Millisecond", 
                        "dimensions": [],
                        "types" : [self.deviceDisplay["type"]] }
            self._registerDTMetric(metric["timeseriesId"], metric)           
            p = subprocess.Popen(["ping", self.deviceAuth["host"], "-c", "4"], stdout = subprocess.PIPE)
            pingStr = p.communicate()[0]
            m = re.search(r"[^*]+rtt\s([^\\]+)", str(pingStr))
            if m is None:
                return
            ttlStr = m.group(1)
            m = re.search(r"([^\s]+)\s=\s([^\s]+)", ttlStr)
            if m is None:
                return
            aggs = m.group(1).split("/")
            ttls = m.group(2).split("/")
            latency = {
                "timeseriesId": ("%s%s%s" % (self.timeSeriesIdPrefix, ".ping.", "latency.pollinghost")),
                "dataPoints": []
            }
            t_now = int(time.time() * 1000)
            for i, item in enumerate(aggs):
                if item == "avg" or item =="mdev":
                    continue
                latency["dataPoints"].append([t_now, float(ttls[i])])
                t_now += 10
            series = [latency]
            self._sendMetricInBulk(series, bulkSize=1)
        except Exception as e:
            logging.error("Cannot process ping data. Error: %s", e)  
            
