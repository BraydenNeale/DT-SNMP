from dtmon.dtqradar import DTQradarMon

def main():
	dtendpoint = {
		"url": "<DT_URL>",
		"apiToken": "<API_TOKEN>" #Dev
	}
	
	qradarEndpoint = {
		"host": "<IP>",
		"port": 161,
		"snmpAuth": {
			"version": 3,
			"username": "<USER>",
			"authKey": "<AUTH_KEY>",
			"authProtocol": "<AUTH_PROT>"
		}
	}
	
	deviceDisplay = {
		"id": "<DOMAIN>.qradar.<HOST_NAME>", 
		"displayName": "<HOST_NAME> | Qradar",
		"type": "Qradar",
		"ipAddresses":["<IP>"], 
		"listenPorts":["<PORT>"], 
#		"configUrl":"",
		"tags": ["Qradar", "Cyber", "IBM"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "Qradar",
		"properties": {}
	}

	
	
	logDetails = {"level":"debug", "location": "./DTQradarSNMPMon.log"}
	
	qradar = DTQradarMon(dtendpoint, qradarEndpoint, deviceDisplay, logDetails=logDetails, getLatency=True, mib={"use": False})
	t_qradar = qradar.dtrun()
	t_qradar.join()

	return
	
if __name__ == '__main__':
  main()		