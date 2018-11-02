from .dtmonitoringsnmp import DTSNMPMonitoring
from .dtsnmpifmib import DTIfMibMon
from .dtsnmpciscoprocessmemmib import DTCiscoProcessMon
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import *
import requests, time, datetime, sched, random
import re
import logging
import threading
import json

class DTCiscoMon(DTSNMPMonitoring):
	'''
	propsUmbrella = '1.3.6.1.2.1.1';
	propsMap  = [
		{"properyName" : "Up time", "detailedOid":".3.0"},
		{"properyName" : "System Name", "detailedOid":".5.0"},
		{"properyName" : "Data Center", "detailedOid":".6.0"}
	];
	'''
	
	cpuUmbrella = "1.3.6.1.4.1.9.9.109.1.1.1.1.7"
	memoryFreeUmbrella = "1.3.6.1.4.1.9.9.221.1.1.1.1.8"
	memoryUsedUmbrella = "1.3.6.1.4.1.9.9.221.1.1.1.1.7"

	metricBulkSize = 100
	ifMib = None
	ciscoProcessMib = None

	def __init__(self,
				dtEndpoint,
				deviceAuth,
				deviceDisplay,
				timeout={"dtserver": 10,
				            "device": 10},
				logDetails={"level":"error",
				            "location": "./dtCiscoSNMPMon.log"},
				mib={"use": False},
				useIfAlias=False,
				getLatency=False,
				tsPrefix="domain.cisco.generic"):
		super(DTCiscoMon, self).__init__(dtEndpoint, 
							deviceAuth, 
							deviceDisplay, 
							timeout=timeout, 
							logDetails=logDetails, 
							mib=mib,
							tsPrefix=tsPrefix,
							getLatency=getLatency)
		self.ciscoProcessMib = DTCiscoProcessMon(dtEndpoint, 
							deviceAuth, 
							deviceDisplay, 
							timeout=timeout, 
							logDetails=logDetails, 
							mib=mib, 
							tsPrefix=tsPrefix,
							metrics={"memory": True, "cpu": True},
							bulkSize=200)					
		self.ifMib = DTIfMibMon(dtEndpoint, 
							deviceAuth, 
							deviceDisplay, 
							timeout=timeout, 
							logDetails=logDetails, 
							mib=mib, 
							tsPrefix=tsPrefix,
							useIfAlias = useIfAlias,
							bulkSize=200)				

	def dtrun(self):	
		tThread = threading.Thread(target=self.__runThread)
		tThread.start()
		tThread.join()
		return tThread

	def __runThread(self):	
		t1 = threading.Thread(target=self.__tProcessCpuMemory)
		t2 = threading.Thread(target=self.__tProcessIfMib)
		t2.start()
		t1.start()
		t1.join()
		t2.join()	

	def __tProcessIfMib(self):
		self.ifMib.dtrun()
		
	def __tProcessCpuMemory(self):
		self.ciscoProcessMib.dtrun()