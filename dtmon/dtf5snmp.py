from .dtmonitoringsnmp import DTSNMPMonitoring
from .dtsnmpifmib import DTIfMibMon
from .dtsnmphostresourcemib import DTHostResourcesMibMon
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import *
import requests, time, datetime, sched, random
import re
import logging
import threading
import json

class DTF5Mon(DTSNMPMonitoring):
	'''
	propsUmbrella = '1.3.6.1.2.1.1';
	propsMap  = [
		{"properyName" : "Up time", "detailedOid":".3.0"},
		{"properyName" : "System Name", "detailedOid":".5.0"},
		{"properyName" : "Data Center", "detailedOid":".6.0"}
	];
	'''
	metricBulkSize = 100
	ifMib = None
	hostResMib = None

	def __init__(self,
				dtEndpoint,
				deviceAuth,
				deviceDisplay,
				timeout={"dtserver": 10,
				            "device": 10},
				logDetails={"level":"error",
				            "location": "/tmp/dtF5SNMPMon.log"},
				useIfAlias=False,
				mib={"use": False,
					"locations": ["file:///usr/share/snmp/mibs"],
					"modules": ()},
				getLatency=False):
		super(DTF5Mon, self).__init__(dtEndpoint, 
							deviceAuth, 
							deviceDisplay, 
							timeout=timeout, 
							logDetails=logDetails, 
							tsPrefix="f5",
							mib=mib,
							getLatency=getLatency)
		self.ifMib = DTIfMibMon(dtEndpoint, 
							deviceAuth, 
							deviceDisplay, 
							timeout=timeout, 
							logDetails=logDetails,  
							tsPrefix="f5",
							useIfAlias = useIfAlias,
							mib=mib,
							bulkSize=200)
		self.hostResMib = DTHostResourcesMibMon(dtEndpoint, 
							deviceAuth, 
							deviceDisplay, 
							timeout=timeout, 
							logDetails=logDetails,  
							tsPrefix="f5",
							mib=mib,
							bulkSize=200)


	def dtrun(self):	
		tThread = threading.Thread(target=self.__runThread)
		tThread.start()
		tThread.join()
		return tThread

	def __runThread(self):
		t1 = threading.Thread(target=self.__tProcessHostResMib)
		t1.start()	
		t2 = threading.Thread(target=self.__tProcessIfMib)
		t2.start()
		t1.join()
		t2.join()	

	def __tProcessIfMib(self):
		self.ifMib.dtrun()
	
	def __tProcessHostResMib(self):
		self.hostResMib.dtrun()
		
	