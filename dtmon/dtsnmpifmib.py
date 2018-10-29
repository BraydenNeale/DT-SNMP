from .dtmonitoringsnmp import DTSNMPMonitoring
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import *
import requests, time, datetime, sched, random
import re
import logging
import threading
import json

class DTIfMibMon(DTSNMPMonitoring):
	interfaceName = "1.3.6.1.2.1.31.1.1.1.1"
	interfaceAlias = "1.3.6.1.2.1.31.1.1.1.18"
	interfaceDimentions = {}

	ifHCInOctets = "1.3.6.1.2.1.31.1.1.1.6"
	ifHCOutOctets = "1.3.6.1.2.1.31.1.1.1.10"

	ifInErr = "1.3.6.1.2.1.2.2.1.14"
	ifInDiscard = "1.3.6.1.2.1.2.2.1.13"
	ifInUCast = "1.3.6.1.2.1.31.1.1.1.7"
	ifInMCast = "1.3.6.1.2.1.31.1.1.1.8"
	ifInBCast = "1.3.6.1.2.1.31.1.1.1.9"

	ifOutErr = "1.3.6.1.2.1.2.2.1.20"
	ifOutDiscard = "1.3.6.1.2.1.2.2.1.19"
	ifOutUCast = "1.3.6.1.2.1.31.1.1.1.11"
	ifOutMCast = "1.3.6.1.2.1.31.1.1.1.12"
	ifOutBCast = "1.3.6.1.2.1.31.1.1.1.13"

	useAlias = True

	timeSeriesIdPrefix = None

	bulkSize = 1

	def __init__(self,
				dtEndpoint,
				deviceAuth,
				deviceDisplay,
				timeout={"dtserver": 10,
				            "device": 10},
				logDetails={"level":"error",
				            "location": "./dtifmibmon.log"},
				mib={"use": False},
				useIfAlias=True,
				tsPrefix=None,
				bulkSize=100):
		if mib["use"] == True:
			mib["modules"] = mib["modules"] + ('IF-MIB',)		
		super(DTIfMibMon, self).__init__(dtEndpoint, deviceAuth, deviceDisplay, timeout=timeout, logDetails=logDetails, mib=mib)
		if tsPrefix is not None:
			self.timeSeriesIdPrefix = ("custom:%s" % (tsPrefix))
		self.useAlias = useIfAlias
		self.bulkSize = bulkSize

	def __validateInput(self):
		if self.tsPrefix is None:
			raise ValueError("tsPrefix should not be None. Please specify tsPrefix=<stringValue>")

	def dtrun(self):	
		self.__registerMetrics()
		ifAlias = self.interfaceAlias if self.useAlias == True else None
		self.interfaceDimentions = self._getInterfaceIndexAliasMapping(self.interfaceName, ifAlias)
		
		t1 = threading.Thread(target=self.__tProcessIncomingOctets)
		t2 = threading.Thread(target=self.__tProcessOutgoingOctets)
		t3 = threading.Thread(target=self.__tProcessInboundIssues) 
		t4 = threading.Thread(target=self.__tProcessOutboundIssues) 
		t1.start()
		t2.start()
		t3.start()
		t4.start()
		t1.join()
		t2.join()
		t3.join()
		t4.join()
			

	def __tProcessIncomingOctets(self):	
		#Incoming Octets
		ifHCInOctetsMap = self._getMappingWithIdxPosFromCache("interface", self.ifHCInOctets, self._getIfIdxFloatValueMap)
		series = self.__buildInterfaceTrafficData(ifHCInOctetsMap, ("interface.incomingtraffic"))
		self._sendMetricInBulk(series, bulkSize=self.bulkSize)
		

	def __tProcessOutgoingOctets(self):
		#Outgoing Octets
		ifHCOutOctetsMap = self._getMappingWithIdxPosFromCache("interface", self.ifHCOutOctets, self._getIfIdxFloatValueMap)
		series = self.__buildInterfaceTrafficData(ifHCOutOctetsMap, ("interface.outgoingtraffic"))
		self._sendMetricInBulk(series, bulkSize=self.bulkSize)
	

	def __tProcessInboundIssues(self):		
		results = {}
		try:
			inPackets = self.__buildInPacketsMap()
			inErrs = self.__buildInErrorMap()
			inDiscards = self.__buildInDiscardMap()
			errRate, lossRate = {}, {}
			for key, value in inPackets.items():
				if value == 0.0:
					errRate[key] = 0.0
					lossRate[key] = 0.0
				else:	
					if key in inErrs:
						errRate[key] = (inErrs[key] / value) * 100
					if key in inDiscards:
						lossRate[key] = (inDiscards[key] / value) * 100	
			results = { "errRate":errRate , "lossRate":lossRate }
			series = self.__buildInIssueSeries(results)		
			self._sendMetricInBulk(series, bulkSize=self.bulkSize)
		except Exception as e:
			logging.error("%s - Cannot build complete inbound packet map. Error: %s", self.deviceDisplay["displayName"], e)	

	def __buildInIssueSeries(self, issueMap):
		errRate = issueMap["errRate"]
		lossRate = issueMap["lossRate"]
		errSeries = self.__buildInterfaceTrafficData(errRate, ("interface.incomingerrorrate"))
		lossRateSeries = self.__buildInterfaceTrafficData(lossRate, ("interface.incominglossrate"))
		return (errSeries + lossRateSeries)

	def __buildInPacketsMap(self):
		ifInUCastMap = self._getMappingWithIdxPosFromCache("interface", self.ifInUCast, self._getIfIdxFloatValueMap)
		ifInMCastMap = self._getMappingWithIdxPosFromCache("interface", self.ifInMCast, self._getIfIdxFloatValueMap)
		ifInBCastMap = self._getMappingWithIdxPosFromCache("interface", self.ifInBCast, self._getIfIdxFloatValueMap)
		ifInPackets = {}

		uCastKeys = list(ifInUCastMap.keys())
		mCastKeys = list(ifInMCastMap.keys())
		bCastKeys = list(ifInBCastMap.keys())
		keyList = uCastKeys + [i for i in mCastKeys if i not in uCastKeys]
		keyList = keyList + [i for i in bCastKeys if i not in keyList]

		for key in keyList:
			inUCast = ifInUCastMap[key] if key in ifInUCastMap else 0.0
			inMCast = ifInMCastMap[key] if key in ifInMCastMap else 0.0
			inBCast = ifInBCastMap[key] if key in ifInBCastMap else 0.0
			ifInPackets[key] = inUCast + inMCast + inBCast

		cachedKeyInPackets = "%s.%s" % (self.deviceDisplay["id"], "interface.incomingpackets")
		return self._getAndSetCachedJson(cachedKeyInPackets, ifInPackets)

	def __buildInErrorMap(self):
		ifInErrMap = self._getMappingWithIdxPosFromCache("interface", self.ifInErr, self._getIfIdxFloatValueMap)
		cachedKeyInErrs = "%s.%s" % (self.deviceDisplay["id"], "interface.incomingerrors")
		return self._getAndSetCachedJson(cachedKeyInErrs, ifInErrMap)

	def __buildInDiscardMap(self):
		ifInDiscardMap = self._getMappingWithIdxPosFromCache("interface", self.ifInDiscard, self._getIfIdxFloatValueMap)
		cachedKeyInDiscards = "%s.%s" % (self.deviceDisplay["id"], "interface.incomingdiscards")
		return self._getAndSetCachedJson(cachedKeyInDiscards, ifInDiscardMap)

	def __tProcessOutboundIssues(self):
		results = {}
		try:
			outPackets = self.__buildOutPackets()
			outErrs = self.__buildOutErrMap()
			outDiscards = self.__buildOutDiscardMap()
			errRate, lossRate = {}, {}
			for key, value in outPackets.items():
				if value == 0.0:
					errRate[key] = 0.0
					lossRate[key] = 0.0
				else:	
					if key in outErrs:
						errRate[key] = (outErrs[key] / value) * 100
					if key in outDiscards:
						lossRate[key] = (outDiscards[key] / value) * 100	
			results = { "errRate":errRate , "lossRate":lossRate } 
			series = self.__buildOutIssueSeries(results)		
			self._sendMetricInBulk(series, bulkSize=self.bulkSize)
		except Exception as e:
			logging.error("%s - Cannot build complete inbound packet map. Error: %s", self.deviceDisplay["displayName"], e)		

	def __buildOutIssueSeries(self, issueMap):
		errRate = issueMap["errRate"]
		lossRate = issueMap["lossRate"]
		errSeries = self.__buildInterfaceTrafficData(errRate, ("interface.outgoingerrorrate"))
		lossRateSeries = self.__buildInterfaceTrafficData(lossRate, ("interface.outgoinglossrate"))
		return (errSeries + lossRateSeries)
	

	def __buildOutPackets(self):
		ifOutPackets = {}
		ifOutUCastMap = self._getMappingWithIdxPosFromCache("interface", self.ifOutUCast, self._getIfIdxFloatValueMap)
		ifOutMCastMap = self._getMappingWithIdxPosFromCache("interface", self.ifOutMCast, self._getIfIdxFloatValueMap)
		ifOutBCastMap = self._getMappingWithIdxPosFromCache("interface", self.ifOutBCast, self._getIfIdxFloatValueMap)
		uCastKeys = list(ifOutUCastMap.keys())
		mCastKeys = list(ifOutMCastMap.keys())
		bCastKeys = list(ifOutBCastMap.keys())
		keyList = uCastKeys + [i for i in mCastKeys if i not in uCastKeys]
		keyList = keyList + [i for i in bCastKeys if i not in keyList]

		for key in keyList:
			outUCast = ifOutUCastMap[key] if key in ifOutUCastMap else 0.0
			outMCast = ifOutMCastMap[key] if key in ifOutMCastMap else 0.0
			outBCast = ifOutBCastMap[key] if key in ifOutBCastMap else 0.0
			
			ifOutPackets[key] = outUCast + outMCast + outBCast
		cachedKeyOutPackets = "%s.%s" % (self.deviceDisplay["id"], "interface.outgoingpackets")
		return self._getAndSetCachedJson(cachedKeyOutPackets, ifOutPackets)

	def __buildOutErrMap(self):
		ifOutErrMap = self._getMappingWithIdxPosFromCache("interface", self.ifOutErr, self._getIfIdxFloatValueMap)
		cachedKeyOutErrs = "%s.%s" % (self.deviceDisplay["id"], "interface.outgoingerrors")
		return self._getAndSetCachedJson(cachedKeyOutErrs, ifOutErrMap)

	def __buildOutDiscardMap(self):
		ifOutDiscardMap = self._getMappingWithIdxPosFromCache("interface", self.ifOutDiscard, self._getIfIdxFloatValueMap)
		cachedKeyOutDiscards = "%s.%s" % (self.deviceDisplay["id"], "interface.outgoingdiscards")
		return self._getAndSetCachedJson(cachedKeyOutDiscards, ifOutDiscardMap)

	'''
	This method build
	'''
	def __buildInterfaceTrafficData(self, trafficDict, cKey):
		series = []
		cachedKey = "%s.%s" % (self.deviceDisplay["id"], cKey)
		retrievedData = self._getAndSetCachedJson(cachedKey, trafficDict)
		if(retrievedData is not None):
			tnow = int(time.time() * 1000)
			for (key,value) in trafficDict.items():
				if not key in self.interfaceDimentions:
					continue
				if key in retrievedData:
					t_series = {
						"timeseriesId": ("%s%s%s" % (self.timeSeriesIdPrefix, ".snmp.", cKey)),
						"dimensions" : { "interface" : self.interfaceDimentions[key] },
						"dataPoints": [[tnow, value - retrievedData[key]]]
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
			{"suffix": "snmp.interface.incomingtraffic", 
				"details": { "displayName" : "Incoming Traffic", "unit" : "Byte", "dimensions": ["interface"] }},
			{"suffix": "snmp.interface.outgoingtraffic", 
				"details": { "displayName" : "Outgoing Traffic", "unit" : "Byte", "dimensions": ["interface"] }},
			{"suffix": "snmp.interface.incomingerrorrate", 
				"details": { "displayName" : "Inbound Error Rate", "unit" : "Percent", "dimensions": ["interface"] }},
			{"suffix": "snmp.interface.outgoingerrorrate", 
				"details": { "displayName" : "Outbound Error Rate", "unit" : "Percent", "dimensions": ["interface"] }},
			{"suffix": "snmp.interface.incominglossrate", 
				"details": { "displayName" : "Inbound Loss Rate", "unit" : "Percent", "dimensions": ["interface"] }},
			{"suffix": "snmp.interface.outgoinglossrate", 
				"details": { "displayName" : "Outbound Loss Rate", "unit" : "Percent", "dimensions": ["interface"] }}	
		]
						
		for metric in metricList:
			details = metric["details"]
			details["types"] = [ self.deviceDisplay["type"] ]
			self._registerDTMetric(("%s.%s" % (self.timeSeriesIdPrefix, metric["suffix"])), json=details)