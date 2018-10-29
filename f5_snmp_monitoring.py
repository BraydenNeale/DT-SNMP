from dtmon.dtf5snmp import DTF5Mon

def main():
	dtendpoint = {
		"url": "<DYNATRACE_URL>"
		"apiToken": "<API_TOKEN>"
	}
	
	f5Endpoint = {
		"host": "<IP>",
		"port": "<PORT>",
		"snmpAuth": {
			"version": 2,
			"username": "<COMMUNITY_STRING>"
		}
	}
	
	deviceDisplay = {
		"id": "<DOMAIN>.f5.<HOSTNAME>", 
		"displayName": "<HOSTNAME> | F5", 
		"type": "F5",
		"ipAddresses":["<IP>"], 
		"listenPorts":["<PORT>"], 
#		"configUrl":"",
		"tags": ["F5"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "F5",
		"properties": {}
	}

	logDetails = {"level":"debug", "location": "./DTF5SNMPMon.log"}
	
	f5 = DTF5Mon(dtendpoint, f5Endpoint, deviceDisplay, logDetails=logDetails, getLatency=True, mib={"use": False})
	t_f5 = f5.dtrun()
	t_f5.join()

	return
	
if __name__ == '__main__':
  main()		