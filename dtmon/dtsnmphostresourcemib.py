from .dtmonitoringsnmp import DTSNMPMonitoring
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import *
import requests, time, datetime, sched, random
import re
import logging
import threading
import json

class DTHostResourcesMibMon(DTSNMPMonitoring):
	storageTypeDict = {
		"1.3.6.1.2.1.25.2.1.1": {"name": "hrStorageOther", "tsSuffix": "snmp.host.memoryutilisation.other"},
		"1.3.6.1.2.1.25.2.1.2": {"name": "hrStorageRam", "tsSuffix": "snmp.host.memoryutilisation.ram"},
		"1.3.6.1.2.1.25.2.1.3": {"name": "hrStorageVirtualMemory", "tsSuffix": "snmp.host.memoryutilisation.virtualmemory"},
		"1.3.6.1.2.1.25.2.1.4": {"name": "hrStorageFixedDisk", "tsSuffix": "snmp.host.memoryutilisation.fixeddisk"},
		"1.3.6.1.2.1.25.2.1.5": {"name": "hrStorageRemovableDisk"},
		"1.3.6.1.2.1.25.2.1.6": {"name": "hrStorageFloppyDisk"},
		"1.3.6.1.2.1.25.2.1.7": {"name": "hrStorageCompactDisc"},
		"1.3.6.1.2.1.25.2.1.8": {"name": "hrStorageRamDisk"},
		"1.3.6.1.2.1.25.2.1.9": {"name": "hrStorageFlashMemory"},
		"1.3.6.1.2.1.25.2.1.10": {"name": "hrStorageNetworkDisk"}
	}
	storageTypeUmbrella = "1.3.6.1.2.1.25.2.3.1.2"
	storageDescUmbrella = "1.3.6.1.2.1.25.2.3.1.3"
	storageSizeUmbrella = "1.3.6.1.2.1.25.2.3.1.5"
	storageUsedUmbrella = "1.3.6.1.2.1.25.2.3.1.6"

	processorLoadUmbrella = "1.3.6.1.2.1.25.3.3.1.2"

	metricList = [
		{"suffix": "snmp.host.memoryutilisation.ram", 
			"details": { "displayName" : "Memory Utilisation - Physical", "unit" : "Percent", "dimensions": [] }},
		{"suffix": "snmp.host.memoryutilisation.virtualmemory", 
			"details": { "displayName" : "Memory Utilisation - Virtual", "unit" : "Percent", "dimensions": ["type"] }},
		{"suffix": "snmp.host.memoryutilisation.other", 
			"details": { "displayName" : "Memory Utilisation - Other", "unit" : "Percent", "dimensions": ["type"] }},
		{"suffix": "snmp.host.memoryutilisation.fixeddisk", 
			"details": { "displayName" : "Disk Utilisation", "unit" : "Percent", "dimensions": ["disk"] }},
		{"suffix": "snmp.host.processorload", 
			"details": { "displayName" : "CPU Utilisation", "unit" : "Percent", "dimensions": ["cpuIndex"] }}	
	]

	timeSeriesIdPrefix = None

	bulkSize = 1

	def __init__(self,
				dtEndpoint,
				deviceAuth,
				deviceDisplay,
				timeout={"dtserver": 10,
				            "device": 10},
				logDetails={"level":"error",
				            "location": "./dthostresourcemibmon.log"},
				mib={"use": False},
				tsPrefix="<DOMAIN>.genrichost",
				bulkSize=100):
		if mib["use"] == True:
			mib["modules"] = mib["modules"] + ("HOST-RESOURCES-MIB",)		
		super(DTHostResourcesMibMon, self).__init__(dtEndpoint, deviceAuth, deviceDisplay, timeout=timeout, logDetails=logDetails, mib=mib)
		if tsPrefix is not None:
			self.timeSeriesIdPrefix = ("custom:%s" % (tsPrefix))
		self.bulkSize = bulkSize

	def __validateInput(self):
		if self.tsPrefix is None:
			raise ValueError("tsPrefix should not be None. Please specify tsPrefix=<stringValue>")

	def dtrun(self):	
		self.__registerMetrics()
		t1 = threading.Thread(target=self.__tProcessCpuMemory)
		t1.start()
		t1.join()
			

	def __tProcessCpuMemory(self):
		self.__processMemory()
		self.__processCpu()

	def __processCpu(self):
		processorLoadMap = self._getMappingWithIdxPosFromCache("snmp.host.processorload", self.processorLoadUmbrella, self._getIfIdxFloatValueMap)
		tsDef = self._findByKey(self.metricList, "suffix", "snmp.host.processorload")[0]
		
		series = []
		tnow = int(time.time() * 1000)
		for key, value in processorLoadMap.items():
			dimension = {}
			if len(tsDef["details"]["dimensions"]) > 0:
				dimension = {tsDef["details"]["dimensions"][0] : key}
			series.append({
				"timeseriesId": ("%s.%s" % (self.timeSeriesIdPrefix, tsDef["suffix"])),
				"dimensions" : dimension,
				"dataPoints": [[tnow, value ]]
			})	
		self._sendMetricInBulk(series, self.bulkSize)


	def __processMemory(self):	
		#Incoming Octets
		storageTypeMap, storageDescMap, storageSizeMap, storageUsedMap = {}, {}, {}, {}
		storageTypeMap = self._getMappingWithIdxPosFromCache("snmp.host.memoryutilisation", self.storageTypeUmbrella, self._getIfIdxStringValueMap)
		storageDescMap = self._getMappingWithIdxPosFromCache("snmp.host.memoryutilisation", self.storageDescUmbrella, self._getIfIdxStringValueMap)
		storageSizeMap = self._getMappingWithIdxPosFromCache("snmp.host.memoryutilisation", self.storageSizeUmbrella, self._getIfIdxFloatValueMap)
		storageUsedMap = self._getMappingWithIdxPosFromCache("snmp.host.memoryutilisation", self.storageUsedUmbrella, self._getIfIdxFloatValueMap)
		memType = {}
		for key, value in storageTypeMap.items():
			storageType = self.storageTypeDict[value]
			if "tsSuffix" in storageType:
				tsSuffix = storageType["tsSuffix"]
				if not tsSuffix in memType:
					memType[tsSuffix] = []
				memType[tsSuffix].append(key)

		series = []
		tnow = int(time.time() * 1000)
		for key, arr in memType.items():
			tsDef = self._findByKey(self.metricList, "suffix", key)[0]
			dimensions = tsDef["details"]["dimensions"]
			
			for idx in arr:
				dimension = {}
				if idx in storageUsedMap and idx in storageSizeMap and idx in storageDescMap:		
					if not int(storageSizeMap[idx]) == 0:
						if len(dimensions) > 0:
							dimension = {dimensions[0]: storageDescMap[idx]}
						elif len(dimensions) == 0:
							dimension = {}
						dataVal = float(storageUsedMap[idx])/float(storageSizeMap[idx])*100
						series.append({
							"timeseriesId": ("%s.%s" % (self.timeSeriesIdPrefix, tsDef["suffix"])),
							"dimensions" : dimension,
							"dataPoints": [[tnow, dataVal ]]
						})
		self._sendMetricInBulk(series, self.bulkSize)





	'''
	Method to register all the important metrics of Cisco Switch. This include:
	 - CPU utilisation
	 - Memory Utilisation
	 - Incoming Traffic (octet)
	 - Outgoing Traffic (octet)
	'''

	def __registerMetrics(self):
		for metric in self.metricList:
			details = metric["details"]
			details["types"] = [ self.deviceDisplay["type"] ]
			self._registerDTMetric(("%s.%s" % (self.timeSeriesIdPrefix, metric["suffix"])), json=details)