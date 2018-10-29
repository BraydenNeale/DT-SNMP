from .dtmonitoringsnmp import DTSNMPMonitoring
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import *
import requests, time, datetime, sched, random
import re
import logging
import threading
import json

class DTCiscoProcessMon(DTSNMPMonitoring):
	
	cpuUmbrella = "1.3.6.1.4.1.9.9.109.1.1.1.1.7";
	memoryFreeUmbrella = "1.3.6.1.4.1.9.9.221.1.1.1.1.8"
	memoryUsedUmbrella = "1.3.6.1.4.1.9.9.221.1.1.1.1.7"

	metrics = {"cpu": True, "memory": True}

	bulkSize = 1

	def __init__(self,
				dtEndpoint,
				deviceAuth,
				deviceDisplay,
				timeout={"dtserver": 10,
				            "device": 10},
				logDetails={"level":"error",
				            "location": "./dtCiscoProcessMon.log"},
				mib={"use": False},
				getLatency=False,
				metrics={"cpu": True, "memory": True},
				bulkSize=100,
				tsPrefix="<DOMAIN>.cisco.generic"):
		if mib["use"] == True:
			mib["modules"] = mib["modules"] + ('CISCO-PROCESS-MIB', 'CISCO-ENHANCED-MEMPOOL-MIB')
		super(DTCiscoProcessMon, self).__init__(dtEndpoint, 
							deviceAuth, 
							deviceDisplay, 
							timeout=timeout, 
							logDetails=logDetails, 
							mib=mib,
							tsPrefix=tsPrefix)
		self.metrics = metrics
		self.bulkSize=bulkSize					

	def dtrun(self):	
		tThread = threading.Thread(target=self.__runThread)
		tThread.start()
		tThread.join()

	def __runThread(self):
		self.__registerMetrics()	
		t1 = threading.Thread(target=self.__tProcessCpuMemory)
		t1.start()
		t1.join()	
		
	def __tProcessCpuMemory(self):
		#CPU
		if self.metrics["cpu"] == True:
			cpuMap = self._getMappingWithIdxPosFromCache("device.cpu.utilisation", self.cpuUmbrella, self._getIfIdxFloatValueMap)
			cpuSeries = self.__buildCPUPctData(cpuMap, "device.cpu.utilisation")
			self._sendMetricInBulk(cpuSeries, bulkSize=self.bulkSize)

		#Memory
		if self.metrics["memory"] == True:
			memUsedMap = self._getMappingWithIdxPosFromCache("device.memory.utilisation", self.memoryUsedUmbrella, self._getIfIdxFloatValueMap)
			memFreedMap = self._getMappingWithIdxPosFromCache("device.memory.utilisation", self.memoryFreeUmbrella, self._getIfIdxFloatValueMap)
			memSeries = self.__buildMemoryPctData(memUsedMap, memFreedMap, "device.memory.utilisation")
			self._sendMetricInBulk(memSeries, bulkSize=self.bulkSize)

	def __buildMemoryPctData(self, usedMemDict, freeMemDict, cKey):
		series = []
		for key, value in usedMemDict.items():
			pct = (value * 100) / (value + freeMemDict[key])
			t_series = {
				"timeseriesId": ("%s%s%s" % (self.timeSeriesIdPrefix, ".snmp.", cKey)),
				"dimensions": {"memIndex": str(key).strip()},
				"dataPoints": [[int(time.time() * 1000), pct]]
			}
			series.append(t_series)	
		return series

	
	def __buildCPUPctData(self, cpuDict, cKey):
		series = []
		for key, value in cpuDict.items():
			t_series = {
				"timeseriesId": ("%s%s%s" % (self.timeSeriesIdPrefix, ".snmp.", cKey)),
				"dimensions": {"cpuIndex": str(key).strip()},
				"dataPoints": [[int(time.time() * 1000), value]]
			}
			series.append(t_series)	
		return series


	'''
	Method to register all the important metrics of Cisco Switch. This include:
	 - CPU utilisation
	 - Memory Utilisation
	 - Incoming Traffic (octet)
	 - Outgoing Traffic (octet)
	'''
	def __registerMetrics(self):

		metricList = [
			{"suffix": "snmp.device.cpu.utilisation", 
				"details": { "displayName" : "CPU Utilisation", "unit" : "Percent", "dimensions": ["cpuIndex"] }},
			{"suffix": "snmp.device.memory.utilisation", 
				"details": { "displayName" : "Memory Utilisation", "unit" : "Percent", "dimensions": ["memIndex"] }}
		]
						
		for metric in metricList:
			details = metric["details"]
			details["types"] = [ self.deviceDisplay["type"] ]
			self._registerDTMetric(("%s.%s" % (self.timeSeriesIdPrefix, metric["suffix"])), json=details)