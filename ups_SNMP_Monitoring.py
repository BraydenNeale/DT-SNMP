from dtmon.dtupssnmp import DTUPSMon

def main():
	dtendpoint = {
		"url": "<DT_URL>",
		"apiToken": "<API_TOKEN>"
	}
	
	upsEndpoint = {
		"host": "<IP>",
		"port": 161,
		"snmpAuth": {
			"version": 1,
			"username": "<COMMUNITY_STRING>"
		}
	}
	
	deviceDisplay = {
		"id": "DOMAIN.ups.HOST_NAME", 
		"displayName": "HOST_NAME | UPS", 
		"type": "UPS",
		"ipAddresses":["<IP>"], 
		"listenPorts":["<PORT>"], 
#		"configUrl":"",
		"tags": ["UPS"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "UPS",
		"properties": {}
	}
	
	logDetails = {"level":"info", "location": "./DTUPSSNMPMon.log"}

	ups = DTUPSMon(dtendpoint, vnsoup1Endpoint, vnsoup1Display, logDetails=logDetails)
	t_ups = ups.dtrun()

	ups.join()
	
	return
	
if __name__ == '__main__':
  main()		