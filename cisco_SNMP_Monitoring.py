from dtmon.dtciscosnmp import DTCiscoMon

def main():
	dtendpoint = {
		"url": "<DT_URL>",
		"apiToken": "<DT_API_TOKEN>"
	}
	
	switchEndpoint = {
		"host": "<HOSTNAME / IP>",
		"port": 161,
		"snmpAuth": {
			"version": 2,
			"username": "<COMMUNITY_STRING>"
		}
	}
	
	deviceDisplay = {
		"id": "domain.cisco.switch.<HOSTNAME>", 
		"displayName": "<HOSTNAME> | Cisco Switch", 
		"type": "Cisco Switch",
		"ipAddresses":["<IP>"], 
		"listenPorts":["<PORT>"], 
#		"configUrl":"",
		"tags": ["Cisco Switch", "Cisco", "Switch"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "Cisco Switches",
		"properties": {}
	}

	switchEndpoint2 = {
		"host": "<IP>",
		"port": 161,
		"snmpAuth": {
			"version": 2,
			"username": "<COMMUNITY_STRING>"
		}
	}
	
	deviceDisplay2 = {
		"id": "domain.cisco.switch.<HOSTNAME>", 
		"displayName": "<HOSTNAME> | Cisco Switch", 
		"type": "Cisco Switch",
		"ipAddresses":["<IP>"], 
		"listenPorts":["161"], 
#		"configUrl":"",
		"tags": ["Cisco Switch", "Cisco", "Switch"],
		"favicon":"http://assets.dynatrace.com/global/icons/infographic_rack.png",
		"groupId": "Cisco Switches",
		"properties": {}
	}
	
	logDetails = {"level":"debug", "location": "./DTCiscoSNMPMon.log"}
	tsPrefix="domain.cisco.switch"
	
	switch1 = DTCiscoMon(dtendpoint, switchEndpoint, deviceDisplay, logDetails=logDetails, getLatency=True, tsPrefix=tsPrefix)
	t_switch1 = switch1.dtrun()


	switch2 = DTCiscoMon(dtendpoint, switchEndpoint2, deviceDisplay2, logDetails=logDetails, getLatency=True, tsPrefix=tsPrefix)
	t_switch2 = switch2.dtrun()

	t_switch1.join()
	t_switch2.join()
	
	return
	
if __name__ == '__main__':
  main()		