from .dtmonitoringsnmp import DTSNMPMonitoring
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import *
import requests, time, datetime, sched, random
import re
import logging
import threading
import json

class DTUPSMon(DTSNMPMonitoring):	
	propsUmbrella = '1.3.6.1.4.1.534.1.1';	
	batteryUmbrella = '1.3.6.1.4.1.534.1.2'
	upsInterface = "1.3.6.1.2.1.2.2.1.2"
	interfaceDimentions = {}
	ifInOctets = "1.3.6.1.2.1.2.2.1.10"
	ifOutOctets = "1.3.6.1.2.1.2.2.1.16"
	ifInErrors = "1.3.6.1.2.1.2.2.1.14"
	ifOutErrors = "1.3.6.1.2.1.2.2.1.20"

	timeSeriesIdPrefix = ""

	metricBulkSize = 100

	def __init__(self, 
				dtEndpoint, 
				deviceAuth, 
				deviceDisplay, 
				timeout={"dtserver": 10, "device": 10},
				logDetails={"level":"error", "location": "/tmp/dtISAMSNMPMon.log"},
				mib={"use": True,
				    "locations": ["file:///usr/share/snmp/mibs"],
				    "modules": ('IF-MIB', 'XUPS-MIB',)}):
		super(DTUPSMon, self).__init__(dtEndpoint, deviceAuth, deviceDisplay, timeout=timeout, logDetails=logDetails, mib=mib)
		self.timeSeriesIdPrefix = ("custom:%s" % ("<DOMANI>.ups"))


	def dtrun(self):
		tThread = threading.Thread(target=self.__runThread)
		tThread.start()
		return tThread

	def __runThread(self):
		self.__registerMetrics()
		self.interfaceDimentions = self._getInterfaceIndexAliasMapping(self.upsInterface)

		propsMap  = {};
		iter = self._snmpBulkConnect(self.propsUmbrella)
		self._processIterBulk(iter, self.propsUmbrella, propsMap, self._getStringValueMap)
		props = {}

		if "xupsIdentManufacturer.0" in propsMap:
			props["Manufacturer"] = propsMap["xupsIdentManufacturer.0"]
		if "xupsIdentModel.0" in propsMap:
			props["Model"] = propsMap["xupsIdentModel.0"]
		if "xupsIdentSoftwareVersion.0" in propsMap:
			props["Software Version"] = propsMap["xupsIdentSoftwareVersion.0"]

		self.deviceDisplay["properties"] = props

		series = []

		batteryMap = {}
		iter = self._snmpBulkConnect(self.batteryUmbrella)
		self._processIterBulk(iter, self.batteryUmbrella, batteryMap, self._getStringValueMap)
		if("xupsBatTimeRemaining.0" in batteryMap):
			t_series = {
				"timeseriesId": ("%s%s%s" % (self.timeSeriesIdPrefix, ".snmp.", "ups.battery.timeremaining")),
				"dimensions" : {},
				"dataPoints": [[int(time.time() * 1000), float(batteryMap["xupsBatTimeRemaining.0"])]]
			}
			series.append(t_series)

		ifInOctetsMap = {}
		iter = self._snmpBulkConnect(self.ifInOctets)
		self._processIterBulk(iter, self.ifInOctets, ifInOctetsMap, self._getIfIdxFloatValueMap)
		series = series + self.__buildInterfaceTrafficData(ifInOctetsMap, "interface.incomingtraffic")

		ifOutOctetsMap = {}
		iter = self._snmpBulkConnect(self.ifOutOctets)
		self._processIterBulk(iter, self.ifOutOctets, ifOutOctetsMap, self._getIfIdxFloatValueMap)
		series = series + self.__buildInterfaceTrafficData(ifOutOctetsMap, "interface.outgoingtraffic")

		ifInErrorsMap = {}
		iter = self._snmpBulkConnect(self.ifInErrors)
		self._processIterBulk(iter, self.ifInErrors, ifInErrorsMap, self._getIfIdxFloatValueMap)
		series = series + self.__buildInterfaceTrafficData(ifInErrorsMap, "interface.incomingerror")

		ifOutErrorsMap = {}
		iter = self._snmpBulkConnect(self.ifOutErrors)
		self._processIterBulk(iter, self.ifOutErrors, ifOutErrorsMap, self._getIfIdxFloatValueMap)
		series = series + self.__buildInterfaceTrafficData(ifOutErrorsMap, "interface.outgoingerror")
		self._sendMetricInBulk(series)


	'''
	This method build
	'''
	def __buildInterfaceTrafficData(self, trafficDict, cKey, dataType={"type": "counter", "bit": 64}):
		series = []
		cachedKey = "%s.%s" % (self.deviceDisplay["id"], cKey)
		retrievedData = self._getAndSetCachedJson(cachedKey, trafficDict)
		if(retrievedData is not None):
			tnow = int(time.time() * 1000)
			for (key,value) in trafficDict.items():
				if not key in self.interfaceDimentions:
					continue
				currentValue = value - retrievedData[key]
				if(currentValue < 0):
					if(dataType["bit"] == 32):
						currentValue += 4294967296.0
				t_series = {
					"timeseriesId": ("%s%s%s" % (self.timeSeriesIdPrefix, ".snmp.", cKey)),
					"dimensions" : { "interface" : self.interfaceDimentions[key] },
					"dataPoints": [[tnow, currentValue]]
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
			{"suffix": "snmp.ups.battery.timeremaining", 
				"details": { "displayName" : "Battery Remaining", "unit" : "Second", "dimensions": [] }},
			{"suffix": "snmp.interface.incomingtraffic", 
				"details": { "displayName" : "Incoming Traffic", "unit" : "Byte", "dimensions": ["interface"] }},
			{"suffix": "snmp.interface.outgoingtraffic", 
				"details": { "displayName" : "Outgoing Traffic", "unit" : "Byte", "dimensions": ["interface"] }},			
			{"suffix": "snmp.interface.incomingerror", 
				"details": { "displayName" : "Incoming Errors", "unit" : "Count", "dimensions": ["interface"] }},
			{"suffix": "snmp.interface.outgoingerror", 
				"details": { "displayName" : "Outgoing Errors", "unit" : "Count", "dimensions": ["interface"] }}
		]
						
		for metric in metricList:
			details = metric["details"]
			details["types"] = [ self.deviceDisplay["type"] ]
			self._registerDTMetric(("%s.%s" % (self.timeSeriesIdPrefix, metric["suffix"])), json=details)
